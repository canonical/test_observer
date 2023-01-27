# testcases.api.EnvironmentsApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addenvironments**](EnvironmentsApi.md#addenvironments) | **POST** /environments | Add a new environments
[**deleteenvironments**](EnvironmentsApi.md#deleteenvironments) | **DELETE** /environments/{environmentsId} | Delete a environments
[**getenvironmentsById**](EnvironmentsApi.md#getenvironmentsbyid) | **GET** /environments/{environmentsId} | Get environments by its Id
[**updateenvironments**](EnvironmentsApi.md#updateenvironments) | **PUT** /environments/{environmentsId} | Update an existent environments


# **addenvironments**
> String addenvironments(addenvironmentsRequest)

Add a new environments

Add a new environments to an existend artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = EnvironmentsApi();
final addenvironmentsRequest = AddenvironmentsRequest(); // AddenvironmentsRequest | Create a new environments

try {
    final result = api_instance.addenvironments(addenvironmentsRequest);
    print(result);
} catch (e) {
    print('Exception when calling EnvironmentsApi->addenvironments: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addenvironmentsRequest** | [**AddenvironmentsRequest**](AddenvironmentsRequest.md)| Create a new environments | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteenvironments**
> deleteenvironments(environmentsId)

Delete a environments

Delete a environments in an existent artefact

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = EnvironmentsApi();
final environmentsId = 11111111-1111-1111-1111-111111111111; // String | Id of the environments to delete

try {
    api_instance.deleteenvironments(environmentsId);
} catch (e) {
    print('Exception when calling EnvironmentsApi->deleteenvironments: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environmentsId** | **String**| Id of the environments to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getenvironmentsById**
> Environments getenvironmentsById(environmentsId)

Get environments by its Id

Fetch the environments with all its items

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = EnvironmentsApi();
final environmentsId = 11111111-1111-1111-1111-111111111111; // String | ID of page to return

try {
    final result = api_instance.getenvironmentsById(environmentsId);
    print(result);
} catch (e) {
    print('Exception when calling EnvironmentsApi->getenvironmentsById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environmentsId** | **String**| ID of page to return | 

### Return type

[**Environments**](Environments.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateenvironments**
> updateenvironments(environmentsId, environments)

Update an existent environments

Update an existent environments. Here we should be able to rename the environments and update its items

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = EnvironmentsApi();
final environmentsId = 11111111-1111-1111-1111-111111111111; // String | ID of environments to return
final environments = Environments(); // Environments | Update an existent environments

try {
    api_instance.updateenvironments(environmentsId, environments);
} catch (e) {
    print('Exception when calling EnvironmentsApi->updateenvironments: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **environmentsId** | **String**| ID of environments to return | 
 **environments** | [**Environments**](Environments.md)| Update an existent environments | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

