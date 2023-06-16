import azure.functions as func
from dataclasses import asdict
import asyncio
from dotenv import load_dotenv
from azureOpenAI import azureOpenAI, ChatCompletion, ResultAzureOpenAI, RequestAzureOpenAI, ChatCompletionArray
import json
import os
import uuid
from cosmosdb import cosmosdb
import logging
load_dotenv()

completion_format_user = {'role' : 'user', 'content' : None}
max_token = int(os.getenv('MAX_TOKEN'))
app = func.FunctionApp()
@app.function_name(name="HttpTrigger1")
@app.route(route="hello") # HTTP Trigger
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name=os.getenv('cosmos_database_name'),
                      container_name=os.getenv('cosmos_collections_name'),
                      connection="cosmos_connection_str",
                      create_if_not_exists=True,
                      partition_key="/userid")
def request_openai(req: func.HttpRequest,
                  outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    aoai: azureOpenAI = azureOpenAI.get_instance()
    s : str = req.get_body().decode('utf-8')
    req = json.loads(s)
    cos : cosmosdb = cosmosdb.get_instance()
    history : ChatCompletionArray = cos.gethistory(userid=req['id'], max_token=max_token)
    logging.info(history)
    reqo : RequestAzureOpenAI = RequestAzureOpenAI(req['message'], req['id'], history=history)
    ret : ResultAzureOpenAI = asyncio.run(aoai.requestSQL(reqo))
    responseHeaders : dict[str, str] = {"Access-Control-Allow-Origin": "*"}
    if ret.result is not None:
        uuida : str = str(uuid.uuid4())
        completion_format_user['content'] = req['message']
        cosmosoutput = {'id': f"{uuida}", 'userid': req['id'], 'total_token': ret.totalToken, 'messages': [completion_format_user, asdict(ret.result[len(ret.result) - 1])]}
        outputDocument.set(func.Document.from_dict(cosmosoutput))
        chatCompletion : ChatCompletion = ret.result[len(ret.result) - 1]
        
        return func.HttpResponse(body=chatCompletion.to_json(ensure_ascii=False), headers=responseHeaders)
    else:
        return func.HttpResponse(body=ret.to_json(ensure_ascii=False), headers=responseHeaders)


@app.function_name(name="HttpLangChainSQL")
@app.route(route="langsql") # HTTP Trigger
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name=os.getenv('cosmos_database_name'),
                      container_name=os.getenv('cosmos_collections_name'),
                      connection="cosmos_connection_str",
                      create_if_not_exists=True,
                      partition_key="/userid")
def request_openai(req: func.HttpRequest,
                  outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    aoai: azureOpenAI = azureOpenAI.get_instance()
    s : str = req.get_body().decode('utf-8')
    req = json.loads(s)
    #cos : cosmosdb = cosmosdb.get_instance()
    #history : ChatCompletionArray = cos.gethistory(userid=req['id'], max_token=max_token)
    #logging.info(history)
    reqo : RequestAzureOpenAI = RequestAzureOpenAI(req['message'], req['id'])
    ret : ResultAzureOpenAI = asyncio.run(aoai.requestSQL(reqo))
    responseHeaders : dict[str, str] = {"Access-Control-Allow-Origin": "*"}
    if ret.result is not None:
        uuida : str = str(uuid.uuid4())
        completion_format_user['content'] = req['message']
        cosmosoutput = {'id': f"{uuida}", 'userid': req['id'], 'total_token': ret.totalToken, 'messages': [completion_format_user, asdict(ret.result[len(ret.result) - 1])]}
        outputDocument.set(func.Document.from_dict(cosmosoutput))
        chatCompletion : ChatCompletion = ret.result[len(ret.result) - 1]
        
        return func.HttpResponse(body=json.dump({'message' : chatCompletion.content}, ensure_ascii=False), headers=responseHeaders)
    else:
        return func.HttpResponse(body=ret.to_json(ensure_ascii=False), headers=responseHeaders)
