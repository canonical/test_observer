# testcases.api.LaneApi

## Load the API package
```dart
import 'package:testcases/api.dart';
```

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**addLane**](LaneApi.md#addlane) | **POST** /lane | Add a new lane
[**deleteLane**](LaneApi.md#deletelane) | **DELETE** /lane/{laneId} | Delete a lane
[**getArtefactsInLane**](LaneApi.md#getartefactsinlane) | **GET** /lane/{laneId}/artefacts | Get all artefacts in the lane
[**getLaneById**](LaneApi.md#getlanebyid) | **GET** /lane/{laneId} | Get JSON representation of the lane by its Id
[**updateLane**](LaneApi.md#updatelane) | **PUT** /lane/{laneId} | Update an existent lane


# **addLane**
> String addLane(addLaneRequest)

Add a new lane

Add a new lane to an existent page. This method should create an empty open lane and return the new lane Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = LaneApi();
final addLaneRequest = AddLaneRequest(); // AddLaneRequest | Create a new lane

try {
    final result = api_instance.addLane(addLaneRequest);
    print(result);
} catch (e) {
    print('Exception when calling LaneApi->addLane: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **addLaneRequest** | [**AddLaneRequest**](AddLaneRequest.md)| Create a new lane | 

### Return type

**String**

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **deleteLane**
> deleteLane(laneId)

Delete a lane

Permanently delete a lane from the page and all artefacts in this lane

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = LaneApi();
final laneId = 00000000-0000-0000-0000-000000000000; // String | lane id to delete

try {
    api_instance.deleteLane(laneId);
} catch (e) {
    print('Exception when calling LaneApi->deleteLane: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **laneId** | **String**| lane id to delete | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getArtefactsInLane**
> List<Artefact> getArtefactsInLane(laneId)

Get all artefacts in the lane

With this method we should be able to fetch all the artefacts (in JSON) from the lane

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = LaneApi();
final laneId = 38400000-8cf0-11bd-b23e-10b96e4ef00d; // String | lane id to search artefacts in

try {
    final result = api_instance.getArtefactsInLane(laneId);
    print(result);
} catch (e) {
    print('Exception when calling LaneApi->getArtefactsInLane: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **laneId** | **String**| lane id to search artefacts in | 

### Return type

[**List<Artefact>**](Artefact.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **getLaneById**
> Lane getLaneById(laneId)

Get JSON representation of the lane by its Id

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = LaneApi();
final laneId = 00000000-0000-0000-0000-000000000000; // String | ID of page to return

try {
    final result = api_instance.getLaneById(laneId);
    print(result);
} catch (e) {
    print('Exception when calling LaneApi->getLaneById: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **laneId** | **String**| ID of page to return | 

### Return type

[**Lane**](Lane.md)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: Not defined
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **updateLane**
> updateLane(laneId, lane)

Update an existent lane

With this method we should be able move lane to another page (by updating pageId), chage its name and status (maybe also Id itself). If we close a lane, the artefacts in it should also be closed

### Example
```dart
import 'package:testcases/api.dart';
// TODO Configure API key authorization: api_key
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKey = 'YOUR_API_KEY';
// uncomment below to setup prefix (e.g. Bearer) for API key, if needed
//defaultApiClient.getAuthentication<ApiKeyAuth>('api_key').apiKeyPrefix = 'Bearer';

final api_instance = LaneApi();
final laneId = 00000000-0000-0000-0000-000000000000; // String | ID of lane to return
final lane = Lane(); // Lane | Update an existent lane

try {
    api_instance.updateLane(laneId, lane);
} catch (e) {
    print('Exception when calling LaneApi->updateLane: $e\n');
}
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **laneId** | **String**| ID of lane to return | 
 **lane** | [**Lane**](Lane.md)| Update an existent lane | 

### Return type

void (empty response body)

### Authorization

[api_key](../README.md#api_key)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: Not defined

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

