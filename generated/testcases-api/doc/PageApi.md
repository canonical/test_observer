# testcases.api.PageApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addPage**](PageApi.md#addpage) | **POST** /page | Add a new page of build artefacts
[**deletePage**](PageApi.md#deletepage) | **DELETE** /page/{pageId} | Delete a page
[**getArtefactsOnPage**](PageApi.md#getartefactsonpage) | **GET** /page/{pageId}/artefacts | Get all artefacts on the page
[**getLanesOnPage**](PageApi.md#getlanesonpage) | **GET** /page/{pageId}/lanes | Get all lanes on the page
[**getPageById**](PageApi.md#getpagebyid) | **GET** /page/{pageId} | Fetch a page by ID
[**updatePage**](PageApi.md#updatepage) | **PUT** /page/{pageId} | Update an existent page


# **addPage**
> String addPage(addPageRequest)

Add a new page of build artefacts

Create a new page. Here we specify the page name, the status of the page is open. The response should contian of page ID

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final addPageRequest = AddPageRequest(); // AddPageRequest | A new page description

try {
    final result = api_instance.addPage(addPageRequest);
    print(result);
} catch (e) {
    print('Exception when calling PageApi->addPage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addPageRequest** | [**AddPageRequest**](AddPageRequest.md)| A new page description | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deletePage**
> deletePage(pageId)

Delete a page

Permanently delete an existing page

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final pageId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | page Id to delete

try {
    api_instance.deletePage(pageId);
} catch (e) {
    print('Exception when calling PageApi->deletePage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pageId** | **String**| page Id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getArtefactsOnPage**
> List<Artefact> getArtefactsOnPage(pageId)

Get all artefacts on the page

Returns an array of artefacts on the page

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final pageId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of page to return

try {
    final result = api_instance.getArtefactsOnPage(pageId);
    print(result);
} catch (e) {
    print('Exception when calling PageApi->getArtefactsOnPage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pageId** | **String**| ID of page to return | 

### Return type

[**List<Artefact>**](Artefact.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLanesOnPage**
> List<Lane> getLanesOnPage(pageId)

Get all lanes on the page

Returns an array of lanes on the page

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final pageId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of page to return

try {
    final result = api_instance.getLanesOnPage(pageId);
    print(result);
} catch (e) {
    print('Exception when calling PageApi->getLanesOnPage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pageId** | **String**| ID of page to return | 

### Return type

[**List<Lane>**](Lane.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getPageById**
> Page getPageById(pageId)

Fetch a page by ID

Returns a single page JSON representation

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final pageId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of page to return

try {
    final result = api_instance.getPageById(pageId);
    print(result);
} catch (e) {
    print('Exception when calling PageApi->getPageById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pageId** | **String**| ID of page to return | 

### Return type

[**Page**](Page.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updatePage**
> updatePage(pageId, page)

Update an existent page

With this method we should be able to update page name and status (and maybe id). If we close the page here, the artefacts and lanes on it should also be closed

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = PageApi();
final pageId = 123e4567-e89b-12d3-a456-426614174000; // String | ID of page to return
final page = Page(); // Page | Update an existent page

try {
    api_instance.updatePage(pageId, page);
} catch (e) {
    print('Exception when calling PageApi->updatePage: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **pageId** | **String**| ID of page to return | 
 **page** | [**Page**](Page.md)| Update an existent page | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

