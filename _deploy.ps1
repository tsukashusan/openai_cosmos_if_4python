$tenantId = "<tenantId>"
$subscriptionId = "<subscriptionId>"
$resourceGroupName="<resourceGroupName>"

az login --tenant $tenantId 
az account set --subscription $subscriptionId

$cosmosdb_accountName="pwylkxjc624ug-cosmos-nosql"
$cosmos_connection_str__accountEndpoint="https://${cosmosdb_accountName}.documents.azure.com:443/"
$AZURE_OPENAI_ENDPOINT="<AZURE_OPENAI_ENDPOINT>"
$AZURE_OPENAI_API_INSTANCE_NAME="<AZURE_OPENAI_API_INSTANCE_NAME>"
$AZURE_OPENAI_API_DEPLOYMENT_NAME="gpt-4o"
$AZURE_OPENAI_API_VERSION="2024-06-01"
$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH="gpt-4o"
$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH=32767
$AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME = "embedding"
$AZURE_OPENAI_MODEL_FOR_EMBEDDING_API = "2024-06-01"
$MAX_TOKEN=16384
$GPT_SYSTEM_SETTING="アシスタントは役に立ち、クリエイティブで、賢く、非常にフレンドリー、女性として回答してください。"
$cosmos_database_name="<cosmos_database_name>"
$cosmos_collections_name="<cosmos_collections_name>"
$AzureWebJobsFeatureFlags="EnableWorkerIndexing"
$AzureWebJobsStorage__accountName="<AzureWebJobsStorage__accountName>"
$AzureWebJobsStorage__blobServiceUri="https://${AzureWebJobsStorage__accountName}.blob.core.windows.net"
$ENABLE_ORYX_BUILD="true"
$MS_SQL_HOST="<MS_SQL_HOST>"
$MS_SQL_PORT=1433
$MS_SQL_USERNAME="openailogin"
$MS_SQL_PASSWORD="<MS_SQL_PASSWORD>"
$MS_SQL_DATABASE="openai-sample"
$MS_SQL_INCLUDE_TABLE="仕入先,運送会社,社員,受注,受注明細,商品,商品区分,都道府県,得意先"
$MS_SQL_ODBC_DRIVER="ODBC Driver 18 for SQL Server"
$functionName="<functionName>"
#$slotName="openai-if-python-2"
$DOC_DIRECTORY="documents"
$BLOB_CONTAINER_INDEX=1
$BLOB_PATH_START_INDEX=2
$DEBUG_MODE = $false



$settingsKV = @{
    "AzureWebJobsStorage__accountName"=$AzureWebJobsStorage__accountName
    "AzureWebJobsStorage__blobServiceUri"=$AzureWebJobsStorage__blobServiceUri
    "AZURE_OPENAI_API_INSTANCE_NAME"=$AZURE_OPENAI_API_INSTANCE_NAME
    "AZURE_OPENAI_ENDPOINT"=$AZURE_OPENAI_ENDPOINT
    "AZURE_OPENAI_API_DEPLOYMENT_NAME"=$AZURE_OPENAI_API_DEPLOYMENT_NAME
    "AZURE_OPENAI_API_VERSION"=$AZURE_OPENAI_API_VERSION
    "AZURE_OPENAI_MODEL_FOR_DOC_SEARCH"=$AZURE_OPENAI_MODEL_FOR_DOC_SEARCH
    "AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH"=$AZURE_OPENAI_MAX_TOKEN_FOR_DOC_SEARCH
    "AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME"=$AZURE_OPENAI_MODEL_FOR_EMBEDDING_NAME
    "AZURE_OPENAI_MODEL_FOR_EMBEDDING_API"=$AZURE_OPENAI_MODEL_FOR_EMBEDDING_API
    "DOC_DIRECTORY"=$DOC_DIRECTORY
    "MAX_TOKEN"=$MAX_TOKEN
    "GPT_SYSTEM_SETTING"=$GPT_SYSTEM_SETTING
    "cosmos_database_name"=$cosmos_database_name
    "cosmos_collections_name"=$cosmos_collections_name
    "cosmos_connection_str__accountEndpoint"=$cosmos_connection_str__accountEndpoint
    "AzureWebJobsFeatureFlags"=$AzureWebJobsFeatureFlags
    "ENABLE_ORYX_BUILD"=$ENABLE_ORYX_BUILD
    "MS_SQL_HOST"=$MS_SQL_HOST
    "MS_SQL_PORT"=$MS_SQL_PORT
    "MS_SQL_USERNAME"=$MS_SQL_USERNAME
    "MS_SQL_PASSWORD"=$MS_SQL_PASSWORD
    "MS_SQL_DATABASE"=$MS_SQL_DATABASE
    "MS_SQL_INCLUDE_TABLE"=$MS_SQL_INCLUDE_TABLE
    "MS_SQL_ODBC_DRIVER"=$MS_SQL_ODBC_DRIVER
    "BLOB_CONTAINER_INDEX"=$BLOB_CONTAINER_INDEX
    "BLOB_PATH_START_INDEX"=$BLOB_PATH_START_INDEX
    "DEBUG_MODE"=$DEBUG_MODE
}

$settingsKV|ConvertTo-Json -Compress|Out-File -FilePath .\setting.json
az functionapp config appsettings set --resource-group $resourceGroupName --name $functionName --settings "@setting.json"
Remove-Item .\setting.json

$include = @("azureOpenAI.py","cosmosdb.py","function_app.py","host.json","langchainDocument.py","requirements.txt")
$pyfiles = Get-ChildItem -Path .\* -Include $include -Force
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