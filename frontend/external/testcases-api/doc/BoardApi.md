# testcases.api.BoardApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addBoard**](BoardApi.md#addboard) | **POST** /board | Add a new board
[**deleteBoard**](BoardApi.md#deleteboard) | **DELETE** /board/{boardId} | Delete a board
[**getBoardById**](BoardApi.md#getboardbyid) | **GET** /board/{boardId} | Fetch a board by ID
[**getCardsOnBoard**](BoardApi.md#getcardsonboard) | **GET** /board/{boardId}/cards | Get all cards on the board
[**getListsOnBoard**](BoardApi.md#getlistsonboard) | **GET** /board/{boardId}/lists | Get all lists on the board
[**updateBoard**](BoardApi.md#updateboard) | **PUT** /board/{boardId} | Update an existent board


# **addBoard**
> String addBoard(addBoardRequest)

Add a new board

Create a new board. Here we specify board name, the status of the board is open. The response should contian of board ID

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final addBoardRequest = AddBoardRequest(); // AddBoardRequest | A new board description

try {
    final result = api_instance.addBoard(addBoardRequest);
    print(result);
} catch (e) {
    print('Exception when calling BoardApi->addBoard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addBoardRequest** | [**AddBoardRequest**](AddBoardRequest.md)| A new board description | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteBoard**
> deleteBoard(boardId)

Delete a board

Permanently delete an existing board

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final boardId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | board Id to delete

try {
    api_instance.deleteBoard(boardId);
} catch (e) {
    print('Exception when calling BoardApi->deleteBoard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **boardId** | **String**| board Id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getBoardById**
> Board getBoardById(boardId)

Fetch a board by ID

Returns a single board JSON representation

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final boardId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of board to return

try {
    final result = api_instance.getBoardById(boardId);
    print(result);
} catch (e) {
    print('Exception when calling BoardApi->getBoardById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **boardId** | **String**| ID of board to return | 

### Return type

[**Board**](Board.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCardsOnBoard**
> List<Card> getCardsOnBoard(boardId)

Get all cards on the board

Returns an array of cards on the board

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final boardId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of board to return

try {
    final result = api_instance.getCardsOnBoard(boardId);
    print(result);
} catch (e) {
    print('Exception when calling BoardApi->getCardsOnBoard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **boardId** | **String**| ID of board to return | 

### Return type

[**List<Card>**](Card.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getListsOnBoard**
> List<List> getListsOnBoard(boardId)

Get all lists on the board

Returns an array of lists on the board

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final boardId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of board to return

try {
    final result = api_instance.getListsOnBoard(boardId);
    print(result);
} catch (e) {
    print('Exception when calling BoardApi->getListsOnBoard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **boardId** | **String**| ID of board to return | 

### Return type

[**List<List>**](List.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateBoard**
> updateBoard(boardId, board)

Update an existent board

With this method we should be able to update board name and status (and maybe id). If we close the board here, the cards and lists on it should also be closed

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = BoardApi();
final boardId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of board to return
final board = Board(); // Board | Update an existent board

try {
    api_instance.updateBoard(boardId, board);
} catch (e) {
    print('Exception when calling BoardApi->updateBoard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **boardId** | **String**| ID of board to return | 
 **board** | [**Board**](Board.md)| Update an existent board | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

