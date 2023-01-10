# testcases.api.CardApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addCard**](CardApi.md#addcard) | **POST** /card | Add a new card
[**addCommentToCard**](CardApi.md#addcommenttocard) | **POST** /card/{cardId}/comments | Add comment an existent card
[**addLabelToCard**](CardApi.md#addlabeltocard) | **POST** /card/{cardId}/labels | Attach a label an existent card
[**deleteCard**](CardApi.md#deletecard) | **DELETE** /card/{cardId} | Delete a card
[**getCardById**](CardApi.md#getcardbyid) | **GET** /card/{cardId} | Get card by its Id
[**getChecklistsInCard**](CardApi.md#getchecklistsincard) | **GET** /card/{cardId}/checklists | Get card checklists
[**getCommentInCardById**](CardApi.md#getcommentincardbyid) | **GET** /card/{cardId}/comments/{commentId} | Get card comments
[**getCommentsInCard**](CardApi.md#getcommentsincard) | **GET** /card/{cardId}/comments | Get card comments
[**getLabelsInCard**](CardApi.md#getlabelsincard) | **GET** /card/{cardId}/labels | Get card labels
[**updateCard**](CardApi.md#updatecard) | **PUT** /card/{cardId} | Update an existent card


# **addCard**
> String addCard(addCardRequest)

Add a new card

Add a new card to en existent list. With this method we should be able to create an empty open card without any checklists, comments and labels. The response should consist of new card Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final addCardRequest = AddCardRequest(); // AddCardRequest | Create a new card

try {
    final result = api_instance.addCard(addCardRequest);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->addCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addCardRequest** | [**AddCardRequest**](AddCardRequest.md)| Create a new card | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addCommentToCard**
> List<Comment> addCommentToCard(cardId, addCommentToCardRequest)

Add comment an existent card

Add comment an existent card by card Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of card
final addCommentToCardRequest = AddCommentToCardRequest(); // AddCommentToCardRequest | The comment body

try {
    final result = api_instance.addCommentToCard(cardId, addCommentToCardRequest);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->addCommentToCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of card | 
 **addCommentToCardRequest** | [**AddCommentToCardRequest**](AddCommentToCardRequest.md)| The comment body | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **addLabelToCard**
> List<Label> addLabelToCard(cardId, addLabelToCardRequest)

Attach a label an existent card

Create a new label for an existent card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of the card
final addLabelToCardRequest = AddLabelToCardRequest(); // AddLabelToCardRequest | The label body

try {
    final result = api_instance.addLabelToCard(cardId, addLabelToCardRequest);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->addLabelToCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of the card | 
 **addLabelToCardRequest** | [**AddLabelToCardRequest**](AddLabelToCardRequest.md)| The label body | 

### Return type

[**List<Label>**](Label.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteCard**
> deleteCard(cardId)

Delete a card

Delete a card and all its labels, comments and checklists

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | card Id to delete

try {
    api_instance.deleteCard(cardId);
} catch (e) {
    print('Exception when calling CardApi->deleteCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| card Id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCardById**
> Card getCardById(cardId)

Get card by its Id

Get a JSON representation of the card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of card to return

try {
    final result = api_instance.getCardById(cardId);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->getCardById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of card to return | 

### Return type

[**Card**](Card.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getChecklistsInCard**
> List<Checklist> getChecklistsInCard(cardId)

Get card checklists

Fetch the JSON representation of the checklists in a card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | Id of the card

try {
    final result = api_instance.getChecklistsInCard(cardId);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->getChecklistsInCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| Id of the card | 

### Return type

[**List<Checklist>**](Checklist.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCommentInCardById**
> List<Comment> getCommentInCardById(cardId, commentId)

Get card comments

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of the card
final commentId = 5; // int | ID of the comment to return

try {
    final result = api_instance.getCommentInCardById(cardId, commentId);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->getCommentInCardById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of the card | 
 **commentId** | **int**| ID of the comment to return | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getCommentsInCard**
> List<Comment> getCommentsInCard(cardId)

Get card comments

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of board to return

try {
    final result = api_instance.getCommentsInCard(cardId);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->getCommentsInCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of board to return | 

### Return type

[**List<Comment>**](Comment.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLabelsInCard**
> List<Label> getLabelsInCard(cardId)

Get card labels

Fetch the labels in the card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | Id of the card

try {
    final result = api_instance.getLabelsInCard(cardId);
    print(result);
} catch (e) {
    print('Exception when calling CardApi->getLabelsInCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| Id of the card | 

### Return type

[**List<Label>**](Label.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateCard**
> updateCard(cardId, card)

Update an existent card

Update an existent card by Id. Here we should be able to move card to another list by changing listId, and update labels and comments as well.

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = CardApi();
final cardId = 11111111-1111-1111-1111-111111111111; // String | ID of card to return
final card = Card(); // Card | Update an existent card

try {
    api_instance.updateCard(cardId, card);
} catch (e) {
    print('Exception when calling CardApi->updateCard: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **cardId** | **String**| ID of card to return | 
 **card** | [**Card**](Card.md)| Update an existent card | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

