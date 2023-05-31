import aiohttp
import os
import json
from dataclasses import dataclass, field, asdict
from dataclasses_json import dataclass_json
from enum import Enum
from dotenv import load_dotenv

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
    history : ChatCompletionArray

@dataclass_json
@dataclass
class ResultAzureOpenAI:
    result : ChatCompletionArray
    error: any = None

class azureOpenAI:
     
    _unique_instance = None

    OPEN_AI_URL : str = "https://%s/openai/deployments/%s/chat/completions?api-version=%s" % (os.getenv('OPEN_AI_URL'), os.getenv('OPEN_AI_MODEL_NAME'), os.getenv('OPEN_AI_API_VERSION'))
    OPEN_AI_KEY : str = os.getenv('OPEN_AI_KEY')
    MAX_TOKEN : int = int(os.getenv('MAX_TOKEN'))
    GPT_SYSTEM_SETTING : str = os.getenv('GPT_SYSTEM_SETTING')


    # 条件2. コンストラクタの可視性をprivateとする。
    ## pythonの場合、コンストラクタをprivate定義できない。
    ## コンストラクタ呼び出しさせず、インスタンス取得をget_instanceに限定する。
    ## get_instanceからインスタンス取得を可能にするため、__init__は使用しない。
    ## 初期化時に、__new__が__init__よりも先に呼び出される。
    def __new__(cls):
        raise NotImplementedError('Cannot Generate Instance By Constructor')

    # インスタンス生成
    @classmethod
    def __internal_new__(cls):
        return super().__new__(cls)

    # 条件3:同じ型のインスタンスを返す `getInstance()` クラスメソッドを定義する。
    @classmethod
    def get_instance(cls):
        # インスタンス未生成の場合
        if not cls._unique_instance:
            cls._unique_instance = cls.__internal_new__()
        return cls._unique_instance

    def __create_msg(self, msg: str, history: ChatCompletionArray ) -> ChatCompletionArray:
        completion = ChatCompletion(Role.USER, msg)
        if history is not None:
            history.messages.append(completion)
            return history
        else:
            completionArray = ChatCompletionArray(
                [
                    ChatCompletion(Role.SYSTEM, self.GPT_SYSTEM_SETTING),
                    ChatCompletion(Role.USER, msg),
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
                    ret = ResultAzureOpenAI([chatCompletion], None)
                    return ret
                else:
                    return ResultAzureOpenAI(None, result['error'])