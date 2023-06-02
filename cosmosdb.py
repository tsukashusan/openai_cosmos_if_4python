import os
from azure.cosmos import CosmosClient, DatabaseProxy, PartitionKey
from azureOpenAI import ChatCompletion, ChatCompletionArray

class cosmosdb:
    _unique_instance = None
    ## コンストラクタ呼び出しさせず、インスタンス取得をget_instanceに限定する。
    ## get_instanceからインスタンス取得を可能にするため、__init__は使用しない。
    ## 初期化時に、__new__が__init__よりも先に呼び出される。
    def __new__(cls):
        raise NotImplementedError('Cannot Generate Instance By Constructor')

    # インスタンス生成
    @classmethod
    def __internal_new__(cls):
        connnection_str: str = os.getenv('cosmos_connection_str')
        cosmos_database_name : str = os.getenv('cosmos_database_name')
        container_name=os.getenv('cosmos_collections_name')
        cosmosClient : CosmosClient = CosmosClient.from_connection_string(connnection_str)
        database :DatabaseProxy = cosmosClient.create_database_if_not_exists(cosmos_database_name)
        cls._container = database.create_container_if_not_exists(container_name, partition_key=PartitionKey("/userid"))
        return super().__new__(cls)

    # 同じ型のインスタンスを返す `getInstance()` クラスメソッドを定義する。
    @classmethod
    def get_instance(cls):
        # インスタンス未生成の場合
        if not cls._unique_instance:
            cls._unique_instance = cls.__internal_new__()
        return cls._unique_instance
    
    def __gettotal_token(self, userid: str, counter: int = 0) -> int:
        query : str
        r = counter
        query = f'SELECT VALUE COUNT(1) FROM c WHERE c.userid="{userid}"'
        for item in cosmosdb._container.query_items(query=query, enable_cross_partition_query=True):
            r = item
            break

        if 0 == r:
            return 0, 0
        elif 1 == r:
            query = f'SELECT VALUE SUM(c.total_token) FROM c WHERE c.userid="{userid}" ORDER BY c._ts ASC'
        else:
            r = r - counter
            query = f'SELECT VALUE SUM(r.total_token) FROM (SELECT TOP {r} c.total_token FROM c WHERE c.userid="{userid}" ORDER BY c._ts ASC) as r'        
        
        for item in cosmosdb._container.query_items(query=query, enable_cross_partition_query=True):
            return r, item
        
    def __get_whithin_limit(self, userid: str, max_token:int = 4096) -> tuple[int, int]:
        counter : int = 0
        while True:
            r, m = self.__gettotal_token(userid=userid, counter=counter)
            if r == 0 and m == 0:
                return r
            elif m < max_token:
                return r
            else:
                counter = counter + 1

    def get_histroy_recalculate(self, histroy_list : list, max_token:int):
        sum_value : int = sum(item['total_token'] for item in histroy_list)
        index : int = 1
        l : list = histroy_list
        while max_token < sum_value:
            l = l[index:-1]
            sum_value = sum(item['total_token'] for item in l)
            index = index + 1
        return l

    def gethistory(self, userid: str, max_token:int = 4096) -> ChatCompletionArray:

        query : str = f'SELECT c.total_token, c.messages FROM c WHERE c.userid="{userid}" ORDER BY c._ts ASC '
        retlist : list = []
        for item in cosmosdb._container.query_items(query=query, enable_cross_partition_query=True):
            retlist.append(item)
        
        retlist = self.get_histroy_recalculate(histroy_list= retlist, max_token=max_token)

        retlist = [i['messages'] for i in retlist]
        l = []
        for i in retlist:
            l.extend(i) 

        return ChatCompletionArray([ChatCompletion(i['role'], i['content']) for i in l])
