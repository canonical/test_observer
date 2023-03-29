//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class BoardApi {
  BoardApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new board
  ///
  /// Create a new board. Here we specify board name, the status of the board is open. The response should contian of board ID
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddBoardRequest] addBoardRequest (required):
  ///   A new board description
  Future<Response> addBoardWithHttpInfo(AddBoardRequest addBoardRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/board';

    // ignore: prefer_final_locals
    Object? postBody = addBoardRequest;

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

  /// Add a new board
  ///
  /// Create a new board. Here we specify board name, the status of the board is open. The response should contian of board ID
  ///
  /// Parameters:
  ///
  /// * [AddBoardRequest] addBoardRequest (required):
  ///   A new board description
  Future<String?> addBoard(AddBoardRequest addBoardRequest,) async {
    final response = await addBoardWithHttpInfo(addBoardRequest,);
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

  /// Delete a board
  ///
  /// Permanently delete an existing board
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   board Id to delete
  Future<Response> deleteBoardWithHttpInfo(String boardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/board/{boardId}'
      .replaceAll('{boardId}', boardId);

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

  /// Delete a board
  ///
  /// Permanently delete an existing board
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   board Id to delete
  Future<void> deleteBoard(String boardId,) async {
    final response = await deleteBoardWithHttpInfo(boardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Fetch a board by ID
  ///
  /// Returns a single board JSON representation
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<Response> getBoardByIdWithHttpInfo(String boardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/board/{boardId}'
      .replaceAll('{boardId}', boardId);

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

  /// Fetch a board by ID
  ///
  /// Returns a single board JSON representation
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<Board?> getBoardById(String boardId,) async {
    final response = await getBoardByIdWithHttpInfo(boardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Board',) as Board;
    
    }
    return null;
  }

  /// Get all cards on the board
  ///
  /// Returns an array of cards on the board
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<Response> getCardsOnBoardWithHttpInfo(String boardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/board/{boardId}/cards'
      .replaceAll('{boardId}', boardId);

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

  /// Get all cards on the board
  ///
  /// Returns an array of cards on the board
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<List<Card>?> getCardsOnBoard(String boardId,) async {
    final response = await getCardsOnBoardWithHttpInfo(boardId,);
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

  /// Get all lists on the board
  ///
  /// Returns an array of lists on the board
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<Response> getListsOnBoardWithHttpInfo(String boardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/board/{boardId}/lists'
      .replaceAll('{boardId}', boardId);

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

  /// Get all lists on the board
  ///
  /// Returns an array of lists on the board
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  Future<List<List>?> getListsOnBoard(String boardId,) async {
    final response = await getListsOnBoardWithHttpInfo(boardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<List>') as List)
        .cast<List>()
        .toList();

    }
    return null;
  }

  /// Update an existent board
  ///
  /// With this method we should be able to update board name and status (and maybe id). If we close the board here, the cards and lists on it should also be closed
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  ///
  /// * [Board] board (required):
  ///   Update an existent board
  Future<Response> updateBoardWithHttpInfo(String boardId, Board board,) async {
    // ignore: prefer_const_declarations
    final path = r'/board/{boardId}'
      .replaceAll('{boardId}', boardId);

    // ignore: prefer_final_locals
    Object? postBody = board;

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

  /// Update an existent board
  ///
  /// With this method we should be able to update board name and status (and maybe id). If we close the board here, the cards and lists on it should also be closed
  ///
  /// Parameters:
  ///
  /// * [String] boardId (required):
  ///   ID of board to return
  ///
  /// * [Board] board (required):
  ///   Update an existent board
  Future<void> updateBoard(String boardId, Board board,) async {
    final response = await updateBoardWithHttpInfo(boardId, board,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
