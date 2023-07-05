import aiohttp
import os
from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json
from enum import Enum
from dotenv import load_dotenv
from langchain.llms.openai import OpenAIChat, AzureOpenAI
from langchain import SQLDatabase, SQLDatabaseChain
from langchain.callbacks import get_openai_callback
import logging
from sqlalchemy.engine import URL
import openai
import re
import json

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
    OPEN_AI_URL : str = "https://%s.openai.azure.com/openai/deployments/%s/chat/completions?api-version=%s" % (os.getenv('AZURE_OPENAI_API_INSTANCE_NAME'), os.getenv('AZURE_OPENAI_API_INSTANCE_NAME'), os.getenv('AZURE_OPENAI_API_VERSION'))
    OPEN_AI_KEY : str = os.getenv('AZURE_OPENAI_API_KEY')
    MAX_TOKEN : int = int(os.getenv('MAX_TOKEN'))
    GPT_SYSTEM_SETTING : str = os.getenv('GPT_SYSTEM_SETTING')

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
        connection_url = URL.create(
            "mssql+pyodbc",
            username=os.getenv('MS_SQL_USERNAME'),
            password=os.getenv('MS_SQL_PASSWORD'),
            host=os.getenv('MS_SQL_HOST'),
            port=int(os.getenv('MS_SQL_PORT')),
            database=os.getenv('MS_SQL_DATABASE'),
            query={"driver": "ODBC Driver 17 for SQL Server"})
        db = SQLDatabase.from_uri(database_uri=connection_url, include_tables=os.getenv('MS_SQL_INCLUDE_TABLE').split(','))
        openai.api_type = "azure" 
        openai.api_base = f"https://{os.getenv('AZURE_OPENAI_API_INSTANCE_NAME')}.openai.azure.com/"
        openai.api_version = os.getenv('AZURE_OPENAI_API_VERSION')
        openai.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        llm = OpenAIChat(
            engine=os.getenv('AZURE_OPENAI_API_DEPLOYMENT_NAME'),
            temperature=0
        )
        #llm = AzureOpenAI(
        #    deployment_name=os.getenv('AZURE_OPENAI_API_DEPLOYMENT_NAME'),
        #    temperature=0
        #    )
        db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, verbose=True)
        ret = db_chain.run(request.msg)

        logging.info("before value:%s", ret)

        retjson = None
        if('Question:' in ret and 'SQLQuery:' in ret):
            ret = re.split('Question:|SQLQuery:', ret)
            retjson = {
                'value':  ret[0].strip(),
                'Question' : ret[1].strip(),
                'SQLQuery' : ret[2].strip()
            }
        elif('Question:' in ret):
            ret = re.split('Question:', ret)
            retjson = {
                'value':  ret[0].strip(),
                'Question' : ret[1].strip()
            }
        elif('SQLQuery:' in ret):
            ret = re.split('SQLQuery:', ret)
            retjson = {
                'value':  ret[0].strip(),
                'SQLQuery' : ret[1].strip()
            }
        elif('value:' in ret):
            ret = re.split('value:', ret)
            retjson = {
                'value':  ret[0].strip()
            }
        else:
            retjson = {
                'value':  ret.strip()
            }                   
        logging.info("after value(ret):%s", json.dumps(retjson, ensure_ascii=False))
        logging.info("after value(json):%s", json.dumps(retjson, ensure_ascii=False))

        return ResultAzureOpenAI([ChatCompletion('assistant', retjson['value'])], -1, None)
