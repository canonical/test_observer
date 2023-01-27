# testcases.api.ArtefactGroupApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addArtefactGroup**](ArtefactGroupApi.md#addartefactgroup) | **POST** /artefact_group | Add a new artefact group
[**getenvironmentssInArtefact**](ArtefactGroupApi.md#getenvironmentssinartefact) | **GET** /artefact_group/{artefactGroupId}/environments | Get environments for artefact group


# **addArtefactGroup**
> String addArtefactGroup(addArtefactGroupRequest)

Add a new artefact group

Add a new artefact group to an existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactGroupApi();
final addArtefactGroupRequest = AddArtefactGroupRequest(); // AddArtefactGroupRequest | Create a new artefact group

try {
    final result = api_instance.addArtefactGroup(addArtefactGroupRequest);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactGroupApi->addArtefactGroup: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addArtefactGroupRequest** | [**AddArtefactGroupRequest**](AddArtefactGroupRequest.md)| Create a new artefact group | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getenvironmentssInArtefact**
> List<Environments> getenvironmentssInArtefact(artefactGroupId)

Get environments for artefact group

Fetch the JSON representation of the environments in a artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactGroupApi();
final artefactGroupId = 11111111-1111-1111-1111-111111111111; // String | Id of the artefact

try {
    final result = api_instance.getenvironmentssInArtefact(artefactGroupId);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactGroupApi->getenvironmentssInArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactGroupId** | **String**| Id of the artefact | 

### Return type

[**List<Environments>**](Environments.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

