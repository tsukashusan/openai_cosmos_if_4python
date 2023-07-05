import os
import platform
import logging
from pydantic import BaseModel, Field
from langchain.llms.openai import AzureOpenAI
from langchain.agents import Tool
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.agents import initialize_agent
from langchain.agents import AgentType
import openai
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from azureOpenAI import ResultAzureOpenAI, ChatCompletion

s = platform.system()
agent = None


class DocumentInput(BaseModel):
    question: str = Field()

def requestUsingDocument(msg: str, context):
    global agent
    if agent is None:
        foldername=context.function_directory
        logging.debug(foldername)
        openai.api_type = "azure" 
        openai.api_base = f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/"
        openai.api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')

        llmChat = ChatOpenAI(
            model_kwargs={"engine": os.getenv('AZURE_OPENAI_API_DEPLOYMENT_NAME')},
            temperature=0,
            openai_api_key=openai.api_key
        )
        #llmChat = AzureOpenAI(
        #    temperature=0,
        #    deployment_name=os.getenv('OPEN_AI_MODEL_FOR_CHAT_NAME'),
        #    openai_api_type="azure",
        #    openai_api_version=os.getenv('OPENAI_API_VERSION')
        #    )
        separator = "/"
        if s == 'Windows':
            separator = "\\"

        tools = []
        files = [
            # https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
            {
                "name": "日本民間公益活動連携機構 就業規則", 
                "path": f"{foldername}{separator}{os.getenv('DOC_DIRECTORY')}{separator}rule_16.pdf",
            }, 
            # https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
            {
                "name": "中小規模事業場モデル就業規則", 
                "path": f"{foldername}{separator}{os.getenv('DOC_DIRECTORY')}{separator}syugyoukisoku_model.pdf"
            }
            # https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
            #{
            #    "name": "日本民間公益活動連携機構 就業規則", 
            #    "path": f"https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf",
            #}, 
            ## https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
            #{
            #    "name": "中小規模事業場モデル就業規則", 
            #    "path": f"https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf"
            #}
        ]
        
        for file in files:
            cwd = os.getcwd()
            logging.info(f"curdir={cwd}")
            a = os.path.isfile(file["path"])
            logging.info(f'{file["path"]} is exists : {a}')
            loader = PyPDFLoader(file["path"])
            pages = loader.load_and_split()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = text_splitter.split_documents(pages)
            #embeddings = OpenAIEmbeddings(llm=AzureOpenAI(deployment_name=os.getenv('OPEN_AI_MODEL_FOR_EMBEDDING_NAME'),
            #                                              model='text-embedding-ada-002'))
            #https://github.com/jerryjliu/llama_index/issues/947
            
            embeddings = OpenAIEmbeddings(
                deployment=os.getenv('AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME'),
                model="text-embedding-ada-002",
                openai_api_base=f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/",
                openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                openai_api_type="azure",
                openai_api_version=os.getenv('AZURE_OPENAI_MODEL_FOR_EMBEDDING_API'),
                chunk_size=1
            )
            retriever = FAISS.from_documents(docs, embeddings).as_retriever()
            
            # Wrap retrievers in a Tool
            tools.append(
                Tool(
                    args_schema=DocumentInput,
                    name=file["name"], 
                    description=f"{file['name']}{os.getenv('GPT_SYSTEM_SETTING_FILE')}",
                    func=RetrievalQA.from_chain_type(llm=llmChat, retriever=retriever)
                )
            )

        llm = AzureOpenAI(
            temperature=0,
            openai_api_base=f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/",
            openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            deployment_name=os.getenv('AZURE_OPENAI_MODEL_FOR_DDOC_SEARCH'))
        agent = initialize_agent(
            agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            tools=tools,
            llm=llm,
            verbose=True
        )
    answer = None
    retry = 10
    while 0 < retry:
        try:
            answer = agent({"input": msg})
            break
        except Exception as e:
            if retry != 1:
                logging.warning(e)
            else:
                logging.error(e)
            retry = retry - 1
    return ResultAzureOpenAI([ChatCompletion('assistant', answer['output'])], -1, None)
