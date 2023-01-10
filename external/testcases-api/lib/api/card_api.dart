//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class CardApi {
  CardApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new card
  ///
  /// Add a new card to en existent list. With this method we should be able to create an empty open card without any checklists, comments and labels. The response should consist of new card Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddCardRequest] addCardRequest (required):
  ///   Create a new card
  Future<Response> addCardWithHttpInfo(AddCardRequest addCardRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/card';

    // ignore: prefer_final_locals
    Object? postBody = addCardRequest;

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

  /// Add a new card
  ///
  /// Add a new card to en existent list. With this method we should be able to create an empty open card without any checklists, comments and labels. The response should consist of new card Id
  ///
  /// Parameters:
  ///
  /// * [AddCardRequest] addCardRequest (required):
  ///   Create a new card
  Future<String?> addCard(AddCardRequest addCardRequest,) async {
    final response = await addCardWithHttpInfo(addCardRequest,);
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

  /// Add comment an existent card
  ///
  /// Add comment an existent card by card Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card
  ///
  /// * [AddCommentToCardRequest] addCommentToCardRequest (required):
  ///   The comment body
  Future<Response> addCommentToCardWithHttpInfo(String cardId, AddCommentToCardRequest addCommentToCardRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/comments'
      .replaceAll('{cardId}', cardId);

    // ignore: prefer_final_locals
    Object? postBody = addCommentToCardRequest;

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

  /// Add comment an existent card
  ///
  /// Add comment an existent card by card Id
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card
  ///
  /// * [AddCommentToCardRequest] addCommentToCardRequest (required):
  ///   The comment body
  Future<List<Comment>?> addCommentToCard(String cardId, AddCommentToCardRequest addCommentToCardRequest,) async {
    final response = await addCommentToCardWithHttpInfo(cardId, addCommentToCardRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Comment>') as List)
        .cast<Comment>()
        .toList();

    }
    return null;
  }

  /// Attach a label an existent card
  ///
  /// Create a new label for an existent card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of the card
  ///
  /// * [AddLabelToCardRequest] addLabelToCardRequest (required):
  ///   The label body
  Future<Response> addLabelToCardWithHttpInfo(String cardId, AddLabelToCardRequest addLabelToCardRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/labels'
      .replaceAll('{cardId}', cardId);

    // ignore: prefer_final_locals
    Object? postBody = addLabelToCardRequest;

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

  /// Attach a label an existent card
  ///
  /// Create a new label for an existent card
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of the card
  ///
  /// * [AddLabelToCardRequest] addLabelToCardRequest (required):
  ///   The label body
  Future<List<Label>?> addLabelToCard(String cardId, AddLabelToCardRequest addLabelToCardRequest,) async {
    final response = await addLabelToCardWithHttpInfo(cardId, addLabelToCardRequest,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Label>') as List)
        .cast<Label>()
        .toList();

    }
    return null;
  }

  /// Delete a card
  ///
  /// Delete a card and all its labels, comments and checklists
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   card Id to delete
  Future<Response> deleteCardWithHttpInfo(String cardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}'
      .replaceAll('{cardId}', cardId);

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

  /// Delete a card
  ///
  /// Delete a card and all its labels, comments and checklists
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   card Id to delete
  Future<void> deleteCard(String cardId,) async {
    final response = await deleteCardWithHttpInfo(cardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get card by its Id
  ///
  /// Get a JSON representation of the card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card to return
  Future<Response> getCardByIdWithHttpInfo(String cardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}'
      .replaceAll('{cardId}', cardId);

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

  /// Get card by its Id
  ///
  /// Get a JSON representation of the card
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card to return
  Future<Card?> getCardById(String cardId,) async {
    final response = await getCardByIdWithHttpInfo(cardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Card',) as Card;
    
    }
    return null;
  }

  /// Get card checklists
  ///
  /// Fetch the JSON representation of the checklists in a card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   Id of the card
  Future<Response> getChecklistsInCardWithHttpInfo(String cardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/checklists'
      .replaceAll('{cardId}', cardId);

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

  /// Get card checklists
  ///
  /// Fetch the JSON representation of the checklists in a card
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   Id of the card
  Future<List<Checklist>?> getChecklistsInCard(String cardId,) async {
    final response = await getChecklistsInCardWithHttpInfo(cardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Checklist>') as List)
        .cast<Checklist>()
        .toList();

    }
    return null;
  }

  /// Get card comments
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of the card
  ///
  /// * [int] commentId (required):
  ///   ID of the comment to return
  Future<Response> getCommentInCardByIdWithHttpInfo(String cardId, int commentId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/comments/{commentId}'
      .replaceAll('{cardId}', cardId)
      .replaceAll('{commentId}', commentId.toString());

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

  /// Get card comments
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of the card
  ///
  /// * [int] commentId (required):
  ///   ID of the comment to return
  Future<List<Comment>?> getCommentInCardById(String cardId, int commentId,) async {
    final response = await getCommentInCardByIdWithHttpInfo(cardId, commentId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Comment>') as List)
        .cast<Comment>()
        .toList();

    }
    return null;
  }

  /// Get card comments
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of board to return
  Future<Response> getCommentsInCardWithHttpInfo(String cardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/comments'
      .replaceAll('{cardId}', cardId);

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

  /// Get card comments
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of board to return
  Future<List<Comment>?> getCommentsInCard(String cardId,) async {
    final response = await getCommentsInCardWithHttpInfo(cardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Comment>') as List)
        .cast<Comment>()
        .toList();

    }
    return null;
  }

  /// Get card labels
  ///
  /// Fetch the labels in the card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   Id of the card
  Future<Response> getLabelsInCardWithHttpInfo(String cardId,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}/labels'
      .replaceAll('{cardId}', cardId);

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

  /// Get card labels
  ///
  /// Fetch the labels in the card
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   Id of the card
  Future<List<Label>?> getLabelsInCard(String cardId,) async {
    final response = await getLabelsInCardWithHttpInfo(cardId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Label>') as List)
        .cast<Label>()
        .toList();

    }
    return null;
  }

  /// Update an existent card
  ///
  /// Update an existent card by Id. Here we should be able to move card to another list by changing listId, and update labels and comments as well.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card to return
  ///
  /// * [Card] card (required):
  ///   Update an existent card
  Future<Response> updateCardWithHttpInfo(String cardId, Card card,) async {
    // ignore: prefer_const_declarations
    final path = r'/card/{cardId}'
      .replaceAll('{cardId}', cardId);

    // ignore: prefer_final_locals
    Object? postBody = card;

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

  /// Update an existent card
  ///
  /// Update an existent card by Id. Here we should be able to move card to another list by changing listId, and update labels and comments as well.
  ///
  /// Parameters:
  ///
  /// * [String] cardId (required):
  ///   ID of card to return
  ///
  /// * [Card] card (required):
  ///   Update an existent card
  Future<void> updateCard(String cardId, Card card,) async {
    final response = await updateCardWithHttpInfo(cardId, card,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
