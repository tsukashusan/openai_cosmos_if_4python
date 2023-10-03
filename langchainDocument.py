import os
import platform
import logging
from pydantic import BaseModel, Field
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
from urllib.parse import urlparse


platform_system = platform.system()
agent = None


class DocumentInput(BaseModel):
    question: str = Field()


def _is_valid_url(url: str) -> bool:
    """Check if the url is valid."""
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

async def downloadFromBlob(download_filepath, account_url):
    from azure.identity.aio import ManagedIdentityCredential, ChainedTokenCredential, DefaultAzureCredential
    from azure.storage.blob.aio import BlobServiceClient

    # alternatively, use the credential as an async context manager
    parsed = urlparse(account_url)
    logging.info(f"parsed={parsed}")
    path_array = parsed.path.split('/')
    logging.info(f"path_array={path_array}")
    container_index = int(os.getenv('BLOB_CONTAINER_INDEX'))
    container = path_array[container_index]
    account_url = f"{parsed.scheme}://{parsed.netloc}"
    async with ChainedTokenCredential(ManagedIdentityCredential(), DefaultAzureCredential()) as credential:
        async with BlobServiceClient(account_url=account_url, credential=credential) as blob_service_client:
            async with blob_service_client.get_container_client(container) as containerclient:
                blob_path_start_index = int(os.getenv('BLOB_PATH_START_INDEX'))
                blob_path = '/'.join(path_array[blob_path_start_index:])
                async with containerclient.get_blob_client(blob_path) as blob_client:
                    with open(file=download_filepath, mode="wb") as sample_blob:
                        download_stream = await blob_client.download_blob()
                        a = await download_stream.readall()
                        sample_blob.write(a)
    
async def requestUsingDocument(msg: str, context, debug_mode : bool = False):
    from tempfile import NamedTemporaryFile

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
        #llmChat =AzureChatOpenAI(
        #    max_tokens=os.getenv('AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH'),
        #    temperature=0,
        #    openai_api_base=f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/",
        #    openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        #    openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
        #    deployment_name=os.getenv('AZURE_OPENAI_MODEL_FOR_DOC_SEARCH'))

        separator = "/"
        if platform_system == 'Windows':
            separator = "\\"
        files = None
        if debug_mode:
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
            ]
        else:
            files = [
                ## https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
                #{
                #    "name": "日本民間公益活動連携機構 就業規則", 
                #    "path": f"{foldername}{separator}{os.getenv('DOC_DIRECTORY')}{separator}rule_16.pdf",
                #}, 
                ## https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
                #{
                #    "name": "中小規模事業場モデル就業規則", 
                #    "path": f"{foldername}{separator}{os.getenv('DOC_DIRECTORY')}{separator}syugyoukisoku_model.pdf"
                #}
                ## https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
                #{
                #    "name": "日本民間公益活動連携機構 就業規則", 
                #    "path": f"https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf",
                #}, 
                ## https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
                #{
                #    "name": "中小規模事業場モデル就業規則", 
                #    "path": f"https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf"
                #}
                # https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
                #{
                #    "name": "日本民間公益活動連携機構 就業規則", 
                #    "path": "https://filessearch.blob.core.windows.net/data/rule_16.pdf",
                #}, 
                ## https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
                #{
                #    "name": "中小規模事業場モデル就業規則", 
                #    "path": "https://filessearch.blob.core.windows.net/data/syugyoukisoku_model.pdf"
                #}
                # https://www.janpia.or.jp/about/information/pdf/rule/rule_16.pdf
                {
                    "name": "日本民間公益活動連携機構 就業規則", 
                    "path": "https://filessearch.blob.core.windows.net/data/syugyoukisoku_model.pdf?sp=r&st=2023-07-12T13:16:18Z&se=2100-07-12T21:16:18Z&spr=https&sv=2022-11-02&sr=b&sig=oCzstH0qDJ0lPQ8myENV0pBcKLN5aB3vlXwGjkjseJo%3D",
                }, 
                # https://www.m-sensci.or.jp/_userdata/keieishien/syugyoukisoku_model.pdf
                {
                    "name": "中小規模事業場モデル就業規則", 
                    "path": f"https://filessearch.blob.core.windows.net/data/rule_16.pdf?sp=r&st=2023-07-12T13:17:38Z&se=2100-07-12T21:17:38Z&spr=https&sv=2022-11-02&sr=b&sig=NOpS9uVg1rz5ZfgcG8580I9Pyriw9WNLEco1EQTr%2BW0%3D"
                }
            ]
        tools = []

        for file in files:
            cwd = os.getcwd()
            logging.info(f"curdir={cwd}")
            a = os.path.isfile(file['path'])
            logging.info(f"{file['path']} is exists : {a}")
            if debug_mode:
                file_path = file['path']
            else:
                tmpfile = NamedTemporaryFile(suffix=".pdf")
                file_path = tmpfile.name
                await downloadFromBlob(download_filepath=file_path, account_url=file['path']) if not a and _is_valid_url(file['path']) else file['path']
            logging.info(f"file_path={file_path}")
            loader = PyPDFLoader(file_path)
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
            qa = RetrievalQA.from_chain_type(llm=llmChat, retriever=retriever)
            # Wrap retrievers in a Tool
            tools.append(
                Tool(
                    args_schema=DocumentInput,
                    name=file["name"], 
                    description=f"{file['name']}{os.getenv('GPT_SYSTEM_SETTING_FILE')}",
                    func=RetrievalQA.from_chain_type(llm=llmChat, retriever=retriever)
                )
            )
        llm = AzureChatOpenAI(
            max_tokens=os.getenv('AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH'),
            temperature=0,
            openai_api_base=f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/",
            openai_api_key=os.getenv('AZURE_OPENAI_API_KEY'),
            openai_api_version=os.getenv('AZURE_OPENAI_API_VERSION'),
            deployment_name=os.getenv('AZURE_OPENAI_MODEL_FOR_DOC_SEARCH'))
        agent = initialize_agent(
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
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
