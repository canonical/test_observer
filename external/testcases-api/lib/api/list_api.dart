//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class ListApi {
  ListApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new list
  ///
  /// Add a new list to an existent board. This method should create an empty open list and return the new list Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddListRequest] addListRequest (required):
  ///   Create a new list
  Future<Response> addListWithHttpInfo(AddListRequest addListRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/list';

    // ignore: prefer_final_locals
    Object? postBody = addListRequest;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'POST',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Add a new list
  ///
  /// Add a new list to an existent board. This method should create an empty open list and return the new list Id
  ///
  /// Parameters:
  ///
  /// * [AddListRequest] addListRequest (required):
  ///   Create a new list
  Future<String?> addList(AddListRequest addListRequest,) async {
    final response = await addListWithHttpInfo(addListRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'String',) as String;
    
    }
    return null;
  }

  /// Delete a list
  ///
  /// Permanently delete a list from the board and all cards in this list
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   list id to delete
  Future<Response> deleteListWithHttpInfo(String listId,) async {
    // ignore: prefer_const_declarations
    final path = r'/list/{listId}'
      .replaceAll('{listId}', listId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'DELETE',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Delete a list
  ///
  /// Permanently delete a list from the board and all cards in this list
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   list id to delete
  Future<void> deleteList(String listId,) async {
    final response = await deleteListWithHttpInfo(listId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get all cards in the list
  ///
  /// With this method we should be able to fetch all the cards (in JSON) from the list
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   list id to search cards in
  Future<Response> getCardsInListWithHttpInfo(String listId,) async {
    // ignore: prefer_const_declarations
    final path = r'/list/{listId}/cards'
      .replaceAll('{listId}', listId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get all cards in the list
  ///
  /// With this method we should be able to fetch all the cards (in JSON) from the list
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   list id to search cards in
  Future<List<Card>?> getCardsInList(String listId,) async {
    final response = await getCardsInListWithHttpInfo(listId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Card>') as List)
        .cast<Card>()
        .toList();

    }
    return null;
  }

  /// Get JSON representation of the list by its Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   ID of board to return
  Future<Response> getListByIdWithHttpInfo(String listId,) async {
    // ignore: prefer_const_declarations
    final path = r'/list/{listId}'
      .replaceAll('{listId}', listId);

    // ignore: prefer_final_locals
    Object? postBody;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>[];


    return apiClient.invokeAPI(
      path,
      'GET',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Get JSON representation of the list by its Id
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   ID of board to return
  Future<List?> getListById(String listId,) async {
    final response = await getListByIdWithHttpInfo(listId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'List',) as List;
    
    }
    return null;
  }

  /// Update an existent list
  ///
  /// With this method we should be able move list to another board (by updating boardId), chage its name and status (maybe also Id itself). If we close a list, the cards in it should also be closed
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   ID of list to return
  ///
  /// * [ModelList] modelList (required):
  ///   Update an existent list
  Future<Response> updateListWithHttpInfo(String listId, ModelList modelList,) async {
    // ignore: prefer_const_declarations
    final path = r'/list/{listId}'
      .replaceAll('{listId}', listId);

    // ignore: prefer_final_locals
    Object? postBody = modelList;

    final queryParams = <QueryParam>[];
    final headerParams = <String, String>{};
    final formParams = <String, String>{};

    const contentTypes = <String>['application/json'];


    return apiClient.invokeAPI(
      path,
      'PUT',
      queryParams,
      postBody,
      headerParams,
      formParams,
      contentTypes.isEmpty ? null : contentTypes.first,
    );
  }

  /// Update an existent list
  ///
  /// With this method we should be able move list to another board (by updating boardId), chage its name and status (maybe also Id itself). If we close a list, the cards in it should also be closed
  ///
  /// Parameters:
  ///
  /// * [String] listId (required):
  ///   ID of list to return
  ///
  /// * [ModelList] modelList (required):
  ///   Update an existent list
  Future<void> updateList(String listId, ModelList modelList,) async {
    final response = await updateListWithHttpInfo(listId, modelList,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
