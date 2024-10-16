import aiohttp
import os
from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json
from enum import Enum
from dotenv import load_dotenv
#from langchain_community.chat_models import AzureChatOpenAI
#from langchain_community.utilities.sql_database import SQLDatabase
from langchain_community.utilities import SQLDatabase
from langchain.chains import create_sql_query_chain
from langchain_experimental.sql import SQLDatabaseChain
import logging
from sqlalchemy.engine import URL
#import openai
import re
import json
import pyodbc
import struct
from azure.identity import DefaultAzureCredential
from sqlalchemy import event

load_dotenv()

class Role(str, Enum):
    SYSTEM = "system"
    ASSISTANT = "assistant"
    USER = "user"

@dataclass_json
@dataclass
class ChatCompletion:
    """ ChatCompletionデータクラス
    """
    role: Role
    content: str

@dataclass_json
@dataclass
class ChatCompletionArray:
    messages: list[ChatCompletion] = field(default_factory=list)

@dataclass_json
@dataclass
class RequestAzureOpenAI:
    msg: str
    id : str
    history : ChatCompletionArray = None

@dataclass_json
@dataclass
class ResultAzureOpenAI:
    result : ChatCompletionArray
    totalToken : int
    error: any = None

class azureOpenAI:
     
    _unique_instance = None
    OPEN_AI_URL : str = "https://%s.openai.azure.com/openai/deployments/%s/chat/completions?api-version=%s" % (os.getenv('AZURE_OPENAI_API_INSTANCE_NAME'), os.getenv('AZURE_OPENAI_API_DEPLOYMENT_NAME'), os.getenv('AZURE_OPENAI_API_VERSION'))
    OPEN_AI_KEY : str = os.getenv('AZURE_OPENAI_API_KEY')
    MAX_TOKEN : int = int(os.getenv('MAX_TOKEN'))
    GPT_SYSTEM_SETTING : str = os.getenv('GPT_SYSTEM_SETTING')
    os.environ["OPENAI_API_TYPE"] = "azure"
    os.environ["OPENAI_API_VERSION"] = os.getenv('AZURE_OPENAI_API_VERSION')
    #os.environ["OPENAI_API_KEY"] = OPEN_AI_KEY
    ## コンストラクタ呼び出しさせず、インスタンス取得をget_instanceに限定する。
    ## get_instanceからインスタンス取得を可能にするため、__init__は使用しない。
    ## 初期化時に、__new__が__init__よりも先に呼び出される。
    def __new__(cls):
        raise NotImplementedError('Cannot Generate Instance By Constructor')

    # インスタンス生成
    @classmethod
    def __internal_new__(cls):
        return super().__new__(cls)

    # 同じ型のインスタンスを返す `getInstance()` クラスメソッドを定義する。
    @classmethod
    def get_instance(cls):
        # インスタンス未生成の場合
        if not cls._unique_instance:
            cls._unique_instance = cls.__internal_new__()
        return cls._unique_instance

    def __create_msg(self, msg: str, history: ChatCompletionArray ) -> ChatCompletionArray:
        completion = ChatCompletion(Role.USER.value, msg)
        if history is not None:
            history.messages = [ChatCompletion(Role.SYSTEM.value, self.GPT_SYSTEM_SETTING)] + history.messages
            history.messages.append(completion)
            return history
        else:
            completionArray = ChatCompletionArray(
                [
                    ChatCompletion(Role.SYSTEM.value, self.GPT_SYSTEM_SETTING),
                    completion,
                ]
            )
            return completionArray

    async def request(self, request: RequestAzureOpenAI) -> ResultAzureOpenAI:
        sendmsg : ChatCompletionArray = self.__create_msg(msg=request.msg, history=request.history)
        headers = {
            'content-type': 'application/json',
            'api-key': self.OPEN_AI_KEY,
            }
        msg = asdict(sendmsg)
        body = {
            'user' : request.id,
            'max_tokens' :  self.MAX_TOKEN,
            'messages' : msg['messages']
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(headers=headers, url=self.OPEN_AI_URL, json=body) as resp:
                result = await resp.json()
                if result.get('choices'):
                    o = result['choices'][0]['message']
                    chatCompletion = ChatCompletion(o['role'], o['content'])
                    ret = ResultAzureOpenAI([chatCompletion], result['usage']['total_tokens'], None)
                    return ret
                else:
                    return ResultAzureOpenAI(None, None, result['error'])
                
    async def requestSQL(self, request: RequestAzureOpenAI) -> ResultAzureOpenAI:
        driver = os.getenv('MS_SQL_ODBC_DRIVER')
        connection_url = URL.create(
            "mssql+pyodbc",
            username=os.getenv('MS_SQL_USERNAME'),
            password=os.getenv('MS_SQL_PASSWORD'),
            host=os.getenv('MS_SQL_HOST'),
            port=int(os.getenv('MS_SQL_PORT')),
            database=os.getenv('MS_SQL_DATABASE'),
            query={"driver": driver})
        #connection_url = URL.create(
        #    "mssql+pyodbc",
        #    username=os.getenv('MS_SQL_USERNAME'),
        #    host=os.getenv('MS_SQL_HOST'),
        #    port=int(os.getenv('MS_SQL_PORT')),
        #    database=os.getenv('MS_SQL_DATABASE'),
        #    query={"driver": driver })       
        #authentication = os.getenv('AZURE_SQL_AUTHENTICATION')  # The value should be 'ActiveDirectoryMsi'
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        
        #token_bytes = credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
        #token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
        #SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h

        db = SQLDatabase.from_uri(database_uri=connection_url, include_tables=os.getenv('MS_SQL_INCLUDE_TABLE').split(','))
        #@event.listens_for(db, 'do_connect')
        #def do_connect(dialect, conn_rec, cargs, cparams):
        #    SQL_COPT_SS_ACCESS_TOKEN = 1256  # This connection option is defined by microsoft in msodbcsql.h
        #    creds = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        #    token_url = "https://database.windows.net/"
        #    token = creds.get_token(token_url).token.encode('utf-16-le')
        #    cparams["attrs_before"] = {SQL_COPT_SS_ACCESS_TOKEN: struct.pack(f'=I{len(token)}s', len(token), token)}
        #
        from langchain_openai import AzureChatOpenAI
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        llm = AzureChatOpenAI(
            model=os.getenv("AZURE_OPENAI_API_DEPLOYMENT_NAME"),
            azure_ad_token=token.token
        )

        #from operator import itemgetter
        #
        #from langchain_core.output_parsers import StrOutputParser
        #from langchain_core.prompts import PromptTemplate
        #from langchain_core.runnables import RunnablePassthrough
        #from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
#
        #execute_query = QuerySQLDataBaseTool(db=db)
        #write_query = create_sql_query_chain(llm, db)
        ##Given the following user question, corresponding SQL query, and SQL result, answer the user question.
        #answer_prompt = PromptTemplate.from_template(
        #    """以下のユーザーからの質問、対応する「SQL query」、および「SQL result」が与えられている場合、ユーザーからの質問に日本語で答えてください。
        #Question: {question}
        #SQL Query: {query}
        #SQL Result: {result}
        #Answer: """
        #)
        #
        #answer = answer_prompt | llm | StrOutputParser()
        #chain = (
        #    RunnablePassthrough.assign(query=write_query).assign(
        #        result=itemgetter("query") | execute_query
        #    )
        #    | answer
        #)
        #
        #ret = chain.invoke({"question": request.msg})
        ##db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=True)
        ##db_chain = create_sql_query_chain(llm, db)
        ##ret = db_chain.run(request.msg)
        ##ret = db_chain.invoke({"question": request.msg})
        from langchain_community.agent_toolkits import create_sql_agent
        
        agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)
        ret = agent_executor.invoke(
            {
                "input": request.msg
            }
        )
        logging.info("before value:%s", ret)

        #retjson = None
        #if('Question:' in ret and 'SQLQuery:' in ret):
        #    ret = re.split('Question:|SQLQuery:', ret)
        #    retjson = {
        #        'value':  ret[0].strip(),
        #        'Question' : ret[1].strip(),
        #        'SQLQuery' : ret[2].strip()
        #    }
        #elif('Question:' in ret):
        #    ret = re.split('Question:', ret)
        #    retjson = {
        #        'value':  ret[0].strip(),
        #        'Question' : ret[1].strip()
        #    }
        #elif('SQLQuery:' in ret):
        #    ret = re.split('SQLQuery:', ret)
        #    retjson = {
        #        'value':  ret[0].strip(),
        #        'SQLQuery' : ret[1].strip()
        #    }
        #elif('value:' in ret):
        #    ret = re.split('value:', ret)
        #    retjson = {
        #        'value':  ret[0].strip()
        #    }
        #else:
        #    retjson = {
        #        'value':  ret.strip()
        #    }
        #retjson = ret        
        logging.info("after value(ret):%s", json.dumps(ret, ensure_ascii=False))
        #logging.info("after value(json):%s", json.dumps(retjson, ensure_ascii=False))

        return ResultAzureOpenAI([ChatCompletion('assistant', ret['output'])], -1, None)
