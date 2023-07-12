$tenantId = "<tenantId>"
$subscriptionId = "<subscriptionId>"
$resourceGroupName="<resourceGroupName>"
$cosmos_connection_str="<cosmos_connection_str>"
$AZURE_OPENAI_API_KEY="<AZURE_OPENAI_API_KEY>"
$AZURE_OPENAI_API_INSTANCE_NAME="<AZURE_OPENAI_API_INSTANCE_NAME>"
$AZURE_OPENAI_API_DEPLOYMENT_NAME="<AZURE_OPENAI_API_DEPLOYMENT_NAME>"
$AZURE_OPENAI_API_VERSION="2023-06-01-preview"
$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH="<AZURE_OPENAI_MODEL_FOR_DOC_SEARCH>"
$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH=4096
$MAX_TOKEN=4096
$GPT_SYSTEM_SETTING="アシスタントは役に立ち、クリエイティブで、賢く、非常にフレンドリー、女性として回答してください。"
$cosmos_database_name="<cosmos_database_name>"
$cosmos_collections_name="<cosmos_collections_name>"
$AzureWebJobsFeatureFlags="EnableWorkerIndexing"
$ENABLE_ORYX_BUILD="true"
$MS_SQL_HOST="sqldbsamplejp.database.windows.net"
$MS_SQL_PORT=1433
$MS_SQL_USERNAME="<MS_SQL_USERNAME>"
$MS_SQL_PASSWORD="<MS_SQL_PASSWORD>"
$MS_SQL_DATABASE="<MS_SQL_DATABASE>"
$MS_SQL_INCLUDE_TABLE="仕入先,運送会社,社員,受注,受注明細,商品,商品区分,都道府県,得意先"
$functionName="<functionName>"
$slotName="<slotName>"
$DOC_DIRECTORY="documents"


az login --tenant $tenantId 
az account set --subscription $subscriptionId

az webapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_connection_str=$cosmos_connection_str
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_INSTANCE_NAME=$AZURE_OPENAI_API_INSTANCE_NAME
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_DEPLOYMENT_NAME=$AZURE_OPENAI_API_DEPLOYMENT_NAME
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MODEL_FOR_DOC_SEARCH=$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH=$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH
az webapp config appsettings set --resource-group demo1 --name $functionName --settings DOC_DIRECTORY=$DOC_DIRECTORY
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MAX_TOKEN=$MAX_TOKEN
az webapp config appsettings set --resource-group demo1 --name $functionName --settings GPT_SYSTEM_SETTING=$GPT_SYSTEM_SETTING
az webapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_database_name=$cosmos_database_name
az webapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_collections_name=$cosmos_collections_name
az webapp config appsettings set --resource-group demo1 --name $functionName --settings AzureWebJobsFeatureFlags=$AzureWebJobsFeatureFlags
az webapp config appsettings set --resource-group demo1 --name $functionName --settings ENABLE_ORYX_BUILD=$ENABLE_ORYX_BUILD
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_HOST=$MS_SQL_HOST
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_PORT=$MS_SQL_PORT
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_USERNAME=$MS_SQL_USERNAME
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_PASSWORD=$MS_SQL_PASSWORD
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_DATABASE=$MS_SQL_DATABASE
az webapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_INCLUDE_TABLE=$MS_SQL_INCLUDE_TABLE

$pyfiles = Get-ChildItem -recurse .\* -Include azureOpenAI.py,cosmosdb.py,function_app.py,host.json,requirements.txt,.python_packages -Force
Compress-Archive -Path $pyfiles  -DestinationPath ..\pythonapp.zip -Force
#az functionapp deployment slot list --name $functionName --resource-group $resourceGroupName
#for production
az functionapp deployment source config-zip --resource-group $resourceGroupName --name $functionName --src ..\pythonapp.zip --build-remote true --verbose

#for slot
az functionapp deployment source config-zip --resource-group $resourceGroupName --name $functionName --src ..\pythonapp.zip --slot $slotName --build-remote true --verbose