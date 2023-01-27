# testcases.api.ArtefactApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addArtefact**](ArtefactApi.md#addartefact) | **POST** /artefact | Add a new artefact
[**addCommentToArtefact**](ArtefactApi.md#addcommenttoartefact) | **POST** /artefact/{artefactId}/comments | Add comment an existent artefact
[**addLabelToArtefact**](ArtefactApi.md#addlabeltoartefact) | **POST** /artefact/{artefactId}/labels | Attach a label an existent artefact
[**deleteArtefact**](ArtefactApi.md#deleteartefact) | **DELETE** /artefact/{artefactId} | Delete a artefact
[**getArtefactById**](ArtefactApi.md#getartefactbyid) | **GET** /artefact/{artefactId} | Get artefact by its Id
[**getCommentInArtefactById**](ArtefactApi.md#getcommentinartefactbyid) | **GET** /artefact/{artefactId}/comments/{commentId} | Get artefact comments
[**getCommentsInArtefact**](ArtefactApi.md#getcommentsinartefact) | **GET** /artefact/{artefactId}/comments | Get artefact comments
[**getLabelsInArtefact**](ArtefactApi.md#getlabelsinartefact) | **GET** /artefact/{artefactId}/labels | Get artefact labels
[**updateArtefact**](ArtefactApi.md#updateartefact) | **PUT** /artefact/{artefactId} | Update an existent artefact


# **addArtefact**
> String addArtefact(addArtefactRequest)

Add a new artefact

Add a new artefact to en existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final addArtefactRequest = AddArtefactRequest(); // AddArtefactRequest | Create a new artefact

try {
    final result = api_instance.addArtefact(addArtefactRequest);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->addArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addArtefactRequest** | [**AddArtefactRequest**](AddArtefactRequest.md)| Create a new artefact | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addCommentToArtefact**
> List<Comment> addCommentToArtefact(artefactId, addCommentToArtefactRequest)

Add comment an existent artefact

Add comment an existent artefact by artefact Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of artefact
final addCommentToArtefactRequest = AddCommentToArtefactRequest(); // AddCommentToArtefactRequest | The comment body

try {
    final result = api_instance.addCommentToArtefact(artefactId, addCommentToArtefactRequest);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->addCommentToArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of artefact | 
 **addCommentToArtefactRequest** | [**AddCommentToArtefactRequest**](AddCommentToArtefactRequest.md)| The comment body | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addLabelToArtefact**
> List<Label> addLabelToArtefact(artefactId, addLabelToArtefactRequest)

Attach a label an existent artefact

Create a new label for an existent artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of the artefact
final addLabelToArtefactRequest = AddLabelToArtefactRequest(); // AddLabelToArtefactRequest | The label body

try {
    final result = api_instance.addLabelToArtefact(artefactId, addLabelToArtefactRequest);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->addLabelToArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of the artefact | 
 **addLabelToArtefactRequest** | [**AddLabelToArtefactRequest**](AddLabelToArtefactRequest.md)| The label body | 

### Return type

[**List<Label>**](Label.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteArtefact**
> deleteArtefact(artefactId)

Delete a artefact

Delete a artefact and all its labels, comments and environmentss

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | artefact Id to delete

try {
    api_instance.deleteArtefact(artefactId);
} catch (e) {
    print('Exception when calling ArtefactApi->deleteArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| artefact Id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getArtefactById**
> Artefact getArtefactById(artefactId)

Get artefact by its Id

Get a JSON representation of the artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of artefact to return

try {
    final result = api_instance.getArtefactById(artefactId);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->getArtefactById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of artefact to return | 

### Return type

[**Artefact**](Artefact.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCommentInArtefactById**
> List<Comment> getCommentInArtefactById(artefactId, commentId)

Get artefact comments

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of the artefact
final commentId = 5; // int | ID of the comment to return

try {
    final result = api_instance.getCommentInArtefactById(artefactId, commentId);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->getCommentInArtefactById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of the artefact | 
 **commentId** | **int**| ID of the comment to return | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCommentsInArtefact**
> List<Comment> getCommentsInArtefact(artefactId)

Get artefact comments

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of page to return

try {
    final result = api_instance.getCommentsInArtefact(artefactId);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->getCommentsInArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of page to return | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLabelsInArtefact**
> List<Label> getLabelsInArtefact(artefactId)

Get artefact labels

Fetch the labels in the artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | Id of the artefact

try {
    final result = api_instance.getLabelsInArtefact(artefactId);
    print(result);
} catch (e) {
    print('Exception when calling ArtefactApi->getLabelsInArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| Id of the artefact | 

### Return type

[**List<Label>**](Label.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateArtefact**
> updateArtefact(artefactId, artefact)

Update an existent artefact

Update an existent artefact by Id. Here we should be able to move artefact to another lane by changing laneId, and update labels and comments as well.

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ArtefactApi();
final artefactId = 11111111-1111-1111-1111-111111111111; // String | ID of artefact to return
final artefact = Artefact(); // Artefact | Update an existent artefact

try {
    api_instance.updateArtefact(artefactId, artefact);
} catch (e) {
    print('Exception when calling ArtefactApi->updateArtefact: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **artefactId** | **String**| ID of artefact to return | 
 **artefact** | [**Artefact**](Artefact.md)| Update an existent artefact | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

