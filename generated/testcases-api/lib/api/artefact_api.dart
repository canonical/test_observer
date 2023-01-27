//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class ArtefactApi {
  ArtefactApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new artefact
  ///
  /// Add a new artefact to en existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddArtefactRequest] addArtefactRequest (required):
  ///   Create a new artefact
  Future<Response> addArtefactWithHttpInfo(AddArtefactRequest addArtefactRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact';

    // ignore: prefer_final_locals
    Object? postBody = addArtefactRequest;

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

  /// Add a new artefact
  ///
  /// Add a new artefact to en existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id
  ///
  /// Parameters:
  ///
  /// * [AddArtefactRequest] addArtefactRequest (required):
  ///   Create a new artefact
  Future<String?> addArtefact(AddArtefactRequest addArtefactRequest,) async {
    final response = await addArtefactWithHttpInfo(addArtefactRequest,);
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

  /// Add comment an existent artefact
  ///
  /// Add comment an existent artefact by artefact Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact
  ///
  /// * [AddCommentToArtefactRequest] addCommentToArtefactRequest (required):
  ///   The comment body
  Future<Response> addCommentToArtefactWithHttpInfo(String artefactId, AddCommentToArtefactRequest addCommentToArtefactRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}/comments'
      .replaceAll('{artefactId}', artefactId);

    // ignore: prefer_final_locals
    Object? postBody = addCommentToArtefactRequest;

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

  /// Add comment an existent artefact
  ///
  /// Add comment an existent artefact by artefact Id
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact
  ///
  /// * [AddCommentToArtefactRequest] addCommentToArtefactRequest (required):
  ///   The comment body
  Future<List<Comment>?> addCommentToArtefact(String artefactId, AddCommentToArtefactRequest addCommentToArtefactRequest,) async {
    final response = await addCommentToArtefactWithHttpInfo(artefactId, addCommentToArtefactRequest,);
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

  /// Attach a label an existent artefact
  ///
  /// Create a new label for an existent artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of the artefact
  ///
  /// * [AddLabelToArtefactRequest] addLabelToArtefactRequest (required):
  ///   The label body
  Future<Response> addLabelToArtefactWithHttpInfo(String artefactId, AddLabelToArtefactRequest addLabelToArtefactRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}/labels'
      .replaceAll('{artefactId}', artefactId);

    // ignore: prefer_final_locals
    Object? postBody = addLabelToArtefactRequest;

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

  /// Attach a label an existent artefact
  ///
  /// Create a new label for an existent artefact
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of the artefact
  ///
  /// * [AddLabelToArtefactRequest] addLabelToArtefactRequest (required):
  ///   The label body
  Future<List<Label>?> addLabelToArtefact(String artefactId, AddLabelToArtefactRequest addLabelToArtefactRequest,) async {
    final response = await addLabelToArtefactWithHttpInfo(artefactId, addLabelToArtefactRequest,);
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

  /// Delete a artefact
  ///
  /// Delete a artefact and all its labels, comments and environmentss
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   artefact Id to delete
  Future<Response> deleteArtefactWithHttpInfo(String artefactId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}'
      .replaceAll('{artefactId}', artefactId);

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

  /// Delete a artefact
  ///
  /// Delete a artefact and all its labels, comments and environmentss
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   artefact Id to delete
  Future<void> deleteArtefact(String artefactId,) async {
    final response = await deleteArtefactWithHttpInfo(artefactId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get artefact by its Id
  ///
  /// Get a JSON representation of the artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact to return
  Future<Response> getArtefactByIdWithHttpInfo(String artefactId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}'
      .replaceAll('{artefactId}', artefactId);

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

  /// Get artefact by its Id
  ///
  /// Get a JSON representation of the artefact
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact to return
  Future<Artefact?> getArtefactById(String artefactId,) async {
    final response = await getArtefactByIdWithHttpInfo(artefactId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Artefact',) as Artefact;
    
    }
    return null;
  }

  /// Get artefact comments
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of the artefact
  ///
  /// * [int] commentId (required):
  ///   ID of the comment to return
  Future<Response> getCommentInArtefactByIdWithHttpInfo(String artefactId, int commentId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}/comments/{commentId}'
      .replaceAll('{artefactId}', artefactId)
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

  /// Get artefact comments
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of the artefact
  ///
  /// * [int] commentId (required):
  ///   ID of the comment to return
  Future<List<Comment>?> getCommentInArtefactById(String artefactId, int commentId,) async {
    final response = await getCommentInArtefactByIdWithHttpInfo(artefactId, commentId,);
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

  /// Get artefact comments
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of page to return
  Future<Response> getCommentsInArtefactWithHttpInfo(String artefactId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}/comments'
      .replaceAll('{artefactId}', artefactId);

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

  /// Get artefact comments
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of page to return
  Future<List<Comment>?> getCommentsInArtefact(String artefactId,) async {
    final response = await getCommentsInArtefactWithHttpInfo(artefactId,);
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

  /// Get artefact labels
  ///
  /// Fetch the labels in the artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   Id of the artefact
  Future<Response> getLabelsInArtefactWithHttpInfo(String artefactId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}/labels'
      .replaceAll('{artefactId}', artefactId);

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

  /// Get artefact labels
  ///
  /// Fetch the labels in the artefact
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   Id of the artefact
  Future<List<Label>?> getLabelsInArtefact(String artefactId,) async {
    final response = await getLabelsInArtefactWithHttpInfo(artefactId,);
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

  /// Update an existent artefact
  ///
  /// Update an existent artefact by Id. Here we should be able to move artefact to another lane by changing laneId, and update labels and comments as well.
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact to return
  ///
  /// * [Artefact] artefact (required):
  ///   Update an existent artefact
  Future<Response> updateArtefactWithHttpInfo(String artefactId, Artefact artefact,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact/{artefactId}'
      .replaceAll('{artefactId}', artefactId);

    // ignore: prefer_final_locals
    Object? postBody = artefact;

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

  /// Update an existent artefact
  ///
  /// Update an existent artefact by Id. Here we should be able to move artefact to another lane by changing laneId, and update labels and comments as well.
  ///
  /// Parameters:
  ///
  /// * [String] artefactId (required):
  ///   ID of artefact to return
  ///
  /// * [Artefact] artefact (required):
  ///   Update an existent artefact
  Future<void> updateArtefact(String artefactId, Artefact artefact,) async {
    final response = await updateArtefactWithHttpInfo(artefactId, artefact,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
