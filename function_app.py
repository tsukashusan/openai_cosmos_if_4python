import azure.functions as func
from dataclasses import asdict
import asyncio
from dotenv import load_dotenv
from azureOpenAI import azureOpenAI, ChatCompletion, ResultAzureOpenAI, RequestAzureOpenAI
import json
import os
load_dotenv()

app = func.FunctionApp()
@app.function_name(name="HttpTrigger1")
@app.route(route="hello") # HTTP Trigger
@app.cosmos_db_output(arg_name="outputDocument", 
                      database_name=os.getenv('cosmos_database_name'),
                      container_name=os.getenv('cosmos_collections_name'),
                      connection="cosmos_connection_str",
                      create_if_not_exists=True,
                      partition_key="/id")
def request_openai(req: func.HttpRequest,
                  outputDocument: func.Out[func.Document]) -> func.HttpResponse:
    aoai: azureOpenAI = azureOpenAI.get_instance()
    s = req.get_body().decode('utf-8')
    req = json.loads(s)
    reqo : RequestAzureOpenAI = RequestAzureOpenAI(req['msg'], req['id'], None)
    ret : ResultAzureOpenAI = asyncio.run(aoai.request(reqo))
    if ret.result is not None:
        cosmosoutput = { 'id': req['id'], 'messages': asdict(ret.result[len(ret.result) - 1])}
        outputDocument.set(func.Document.from_dict(cosmosoutput))
        chatCompletion : ChatCompletion = ret.result[len(ret.result) - 1]
        return func.HttpResponse(chatCompletion.to_json(ensure_ascii=False))
    else:
        return func.HttpResponse(ret.to_json(ensure_ascii=False))
