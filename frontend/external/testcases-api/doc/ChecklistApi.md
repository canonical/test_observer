# testcases.api.ChecklistApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addChecklist**](ChecklistApi.md#addchecklist) | **POST** /checklist | Add a new checklist
[**deleteChecklist**](ChecklistApi.md#deletechecklist) | **DELETE** /checklist/{checklistId} | Delete a checklist
[**getChecklistById**](ChecklistApi.md#getchecklistbyid) | **GET** /checklist/{checklistId} | Get checklist by its Id
[**updateChecklist**](ChecklistApi.md#updatechecklist) | **PUT** /checklist/{checklistId} | Update an existent checklist


# **addChecklist**
> String addChecklist(addChecklistRequest)

Add a new checklist

Add a new checklist to an existend card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ChecklistApi();
final addChecklistRequest = AddChecklistRequest(); // AddChecklistRequest | Create a new checklist

try {
    final result = api_instance.addChecklist(addChecklistRequest);
    print(result);
} catch (e) {
    print('Exception when calling ChecklistApi->addChecklist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addChecklistRequest** | [**AddChecklistRequest**](AddChecklistRequest.md)| Create a new checklist | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteChecklist**
> deleteChecklist(checklistId)

Delete a checklist

Delete a checklist in an existent card

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ChecklistApi();
final checklistId = 11111111-1111-1111-1111-111111111111; // String | Id of the checklist to delete

try {
    api_instance.deleteChecklist(checklistId);
} catch (e) {
    print('Exception when calling ChecklistApi->deleteChecklist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **checklistId** | **String**| Id of the checklist to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getChecklistById**
> Checklist getChecklistById(checklistId)

Get checklist by its Id

Fetch the checklist with all its items

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ChecklistApi();
final checklistId = 11111111-1111-1111-1111-111111111111; // String | ID of board to return

try {
    final result = api_instance.getChecklistById(checklistId);
    print(result);
} catch (e) {
    print('Exception when calling ChecklistApi->getChecklistById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **checklistId** | **String**| ID of board to return | 

### Return type

[**Checklist**](Checklist.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateChecklist**
> updateChecklist(checklistId, checklist)

Update an existent checklist

Update an existent checklist. Here we should be able to rename the checklist and update its items

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = ChecklistApi();
final checklistId = 11111111-1111-1111-1111-111111111111; // String | ID of checklist to return
final checklist = Checklist(); // Checklist | Update an existent checklist

try {
    api_instance.updateChecklist(checklistId, checklist);
} catch (e) {
    print('Exception when calling ChecklistApi->updateChecklist: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **checklistId** | **String**| ID of checklist to return | 
 **checklist** | [**Checklist**](Checklist.md)| Update an existent checklist | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

