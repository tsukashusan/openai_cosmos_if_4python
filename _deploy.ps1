$tenantId = "<tenantId>"
$subscriptionId = "<subscriptionId>"
$cosmos_connection_str="<cosmos_connection_str>"
$OPEN_AI_URL="<OPEN_AI_URL>"
$OPEN_AI_KEY="<OPEN_AI_KEY>"
$OPEN_AI_MODEL_NAME="chat"
$OPEN_AI_API_VERSION="2023-05-15"
$MAX_TOKEN=4096
$GPT_SYSTEM_SETTING="アシスタントは役に立ち、クリエイティブで、賢く、非常にフレンドリー、女性として回答してください。"
$cosmos_database_name="<cosmos_database_name>"
$cosmos_collections_name="<cosmos_collections_name>"
$AzureWebJobsFeatureFlags="EnableWorkerIndexing"
$ENABLE_ORYX_BUILD="true"


az login --tenant $tenantId 
az account set --subscription $subscriptionId

az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings cosmos_connection_str=$cosmos_connection_str
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings OPEN_AI_URL=$OPEN_AI_URL
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings OPEN_AI_KEY=$OPEN_AI_KEY
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings OPEN_AI_MODEL_NAME=$OPEN_AI_MODEL_NAME
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings OPEN_AI_API_VERSION=$OPEN_AI_API_VERSION
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings MAX_TOKEN=$MAX_TOKEN
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings GPT_SYSTEM_SETTING=$GPT_SYSTEM_SETTING
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings cosmos_database_name=$cosmos_database_name
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings cosmos_collections_name=$cosmos_collections_name
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings AzureWebJobsFeatureFlags=$AzureWebJobsFeatureFlags
az webapp config appsettings set --resource-group demo1 --name "openai-if-python" --settings ENABLE_ORYX_BUILD=$ENABLE_ORYX_BUILD

$pyfiles = Get-ChildItem -recurse .\* -Include azureOpenAI.py,cosmosdb.py,function_app.py,host.json,requirements.txt,.python_packages -Force
Compress-Archive -Path $pyfiles  -DestinationPath ..\pythonapp.zip -Force
az functionapp deployment source config-zip --resource-group "demo1" --name "openai-if-python" --src ..\pythonapp.zip --build-remote true --verbose