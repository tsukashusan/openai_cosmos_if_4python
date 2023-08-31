$tenantId = "<tenantId>"
$subscriptionId = "<subscriptionId>"
$resourceGroupName="<resourceGroupName>"
$cosmos_connection_str="<cosmos_connection_str>" #AccountEndpoint=https://xxxx.documents.azure.com:443/;AccountKey=xxxx;
$AZURE_OPENAI_API_KEY="<AZURE_OPENAI_API_KEY>"
$AZURE_OPENAI_API_INSTANCE_NAME="<AZURE_OPENAI_API_INSTANCE_NAME>"
$AZURE_OPENAI_API_DEPLOYMENT_NAME="<AZURE_OPENAI_API_DEPLOYMENT_NAME>"
$AZURE_OPENAI_API_VERSION="2023-06-01-preview"
$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH="<AZURE_OPENAI_MODEL_FOR_DOC_SEARCH>"
$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH=4096
$AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME = "<AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME>"
$AZURE_OPENAI_MODEL_FOR_EMBEDDING_API = "2023-05-15"
$MAX_TOKEN=16384
$GPT_SYSTEM_SETTING="アシスタントは役に立ち、クリエイティブで、賢く、非常にフレンドリー、女性として回答してください。"
$cosmos_database_name="<cosmos_database_name>"
$cosmos_collections_name="<cosmos_collections_name>"
$AzureWebJobsFeatureFlags="EnableWorkerIndexing"
$ENABLE_ORYX_BUILD="true"
$MS_SQL_HOST="<MS_SQL_HOST>"
$MS_SQL_PORT=1433
$MS_SQL_USERNAME="<MS_SQL_USERNAME>"
$MS_SQL_PASSWORD="<MS_SQL_PASSWORD>"
$MS_SQL_DATABASE="<MS_SQL_DATABASE>"
$MS_SQL_INCLUDE_TABLE="仕入先,運送会社,社員,受注,受注明細,商品,商品区分,都道府県,得意先"
$functionName="<functionName>"
$slotName="<slotName>"
$DOC_DIRECTORY="documents"
$BLOB_CONTAINER_INDEX=1
$BLOB_PATH_START_INDEX=2


az login --tenant $tenantId 
az account set --subscription $subscriptionId

az functionapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_connection_str=$cosmos_connection_str
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_INSTANCE_NAME=$AZURE_OPENAI_API_INSTANCE_NAME
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_DEPLOYMENT_NAME=$AZURE_OPENAI_API_DEPLOYMENT_NAME
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_API_VERSION=$AZURE_OPENAI_API_VERSION
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MODEL_FOR_DOC_SEARCH=$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH=$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME=$AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AZURE_OPENAI_MODEL_FOR_EMBEDDING_API=$AZURE_OPENAI_MODEL_FOR_EMBEDDING_API
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings DOC_DIRECTORY=$DOC_DIRECTORY
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MAX_TOKEN=$MAX_TOKEN
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings GPT_SYSTEM_SETTING=$GPT_SYSTEM_SETTING
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_database_name=$cosmos_database_name
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings cosmos_collections_name=$cosmos_collections_name
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings AzureWebJobsFeatureFlags=$AzureWebJobsFeatureFlags
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings ENABLE_ORYX_BUILD=$ENABLE_ORYX_BUILD
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_HOST=$MS_SQL_HOST
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_PORT=$MS_SQL_PORT
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_USERNAME=$MS_SQL_USERNAME
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_PASSWORD=$MS_SQL_PASSWORD
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_DATABASE=$MS_SQL_DATABASE
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings MS_SQL_INCLUDE_TABLE=$MS_SQL_INCLUDE_TABLE
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings BLOB_CONTAINER_INDEX=$BLOB_CONTAINER_INDEX
az functionapp config appsettings set --resource-group demo1 --name $functionName --settings BLOB_PATH_START_INDEX=$BLOB_PATH_START_INDEX
$inlude = @("azureOpenAI.py","cosmosdb.py","function_app.py","host.json","langchainDocument.py","requirements.txt")
$pyfiles = Get-ChildItem -Path .\* -Include $inlude -Force
Compress-Archive -Path $pyfiles -DestinationPath ..\pythonapp.zip -Force
az functionapp deployment source config-zip --resource-group $resourceGroupName --name $functionName --src ..\pythonapp.zip --build-remote true --verbose
$startTime = (Get-Date).datetime
Write-Output "開始時間:${startTime}"
do {
    $ret = az functionapp function list -g $resourceGroupName -n $functionName
    if ($ret.length -gt 0 )
    {
        foreach ($item in $ret) {
            Write-Output "${item}"
        }
        
    }
}
while ($ret.length -le 0 )
$endTime = (Get-Date).datetime
Write-Output "終了時間:${endTime}"