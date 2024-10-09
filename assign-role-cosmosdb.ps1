param(
    [parameter()]$TENANT_ID="<TENANT_ID>",
    [parameter()]$SUBSCRIPTOIN_GUID="<SUBSCRIPTOIN_GUID>",
    [parameter()]$resourceGroupName = "<resourceGroupName>",
    [parameter()]$databaseAccountName = '<databaseAccountName>',
    [parameter()]$principalId = '<principalId>',
    [parameter()]$scope = '/',
    [parameter()]$readWriteRoleDefinitionId = '00000000-0000-0000-0000-000000000002'
)

az login -t ${TENANT_ID} --verbose

az account set --subscription ${SUBSCRIPTOIN_GUID} --verbose
#az deployment group create --resource-group ${resourceGroupName} --template-file ${BICEP_FILE} --parameters main.bicepparam --verbose

az cosmosdb sql role assignment create --account-name $databaseAccountName --resource-group $resourceGroupName --scope $scope --principal-id $principalId --role-definition-id $readWriteRoleDefinitionId