# testcases.api.ListApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addList**](ListApi.md#addlist) | **POST** /list | Add a new list
[**deleteList**](ListApi.md#deletelist) | **DELETE** /list/{listId} | Delete a list
[**getCardsInList**](ListApi.md#getcardsinlist) | **GET** /list/{listId}/cards | Get all cards in the list
[**getListById**](ListApi.md#getlistbyid) | **GET** /list/{listId} | Get JSON representation of the list by its Id
[**updateList**](ListApi.md#updatelist) | **PUT** /list/{listId} | Update an existent list


# **addList**
> String addList(addListRequest)

Add a new list

Add a new list to an existent board. This method should create an empty open list and return the new list Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ListApi();
final addListRequest = AddListRequest(); // AddListRequest | Create a new list

try {
    final result = api_instance.addList(addListRequest);
    print(result);
} catch (e) {
    print('Exception when calling ListApi->addList: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addListRequest** | [**AddListRequest**](AddListRequest.md)| Create a new list | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteList**
> deleteList(listId)

Delete a list

Permanently delete a list from the board and all cards in this list

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ListApi();
final listId = 00000000-0000-0000-0000-000000000000; // String | list id to delete

try {
    api_instance.deleteList(listId);
} catch (e) {
    print('Exception when calling ListApi->deleteList: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **listId** | **String**| list id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCardsInList**
> List<Card> getCardsInList(listId)

Get all cards in the list

With this method we should be able to fetch all the cards (in JSON) from the list

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ListApi();
final listId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | list id to search cards in

try {
    final result = api_instance.getCardsInList(listId);
    print(result);
} catch (e) {
    print('Exception when calling ListApi->getCardsInList: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **listId** | **String**| list id to search cards in | 

### Return type

[**List<Card>**](Card.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getListById**
> List getListById(listId)

Get JSON representation of the list by its Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ListApi();
final listId = 00000000-0000-0000-0000-000000000000; // String | ID of board to return

try {
    final result = api_instance.getListById(listId);
    print(result);
} catch (e) {
    print('Exception when calling ListApi->getListById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **listId** | **String**| ID of board to return | 

### Return type

[**List**](List.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateList**
> updateList(listId, modelList)

Update an existent list

With this method we should be able move list to another board (by updating boardId), chage its name and status (maybe also Id itself). If we close a list, the cards in it should also be closed

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ListApi();
final listId = 00000000-0000-0000-0000-000000000000; // String | ID of list to return
final modelList = ModelList(); // ModelList | Update an existent list

try {
    api_instance.updateList(listId, modelList);
} catch (e) {
    print('Exception when calling ListApi->updateList: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **listId** | **String**| ID of list to return | 
 **modelList** | [**ModelList**](ModelList.md)| Update an existent list | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

