# testcases.model.Card

## Load the model package
```dart
import 'package:testcases/api.dart';
```

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**id** | **String** |  | 
**name** | **String** |  | 
**listId** | **String** | ID of the list where the card is located | 
**boardId** | **String** |  | 
**status** | **String** | List status | 
**checklistsIds** | **List<String>** |  | [optional] [default to const []]
**labels** | [**List<Label>**](Label.md) |  | [optional] [default to const []]
**comments** | [**List<Comment>**](Comment.md) |  | [optional] [default to const []]

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


