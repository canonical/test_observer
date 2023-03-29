//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class ChecklistApi {
  ChecklistApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new checklist
  ///
  /// Add a new checklist to an existend card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddChecklistRequest] addChecklistRequest (required):
  ///   Create a new checklist
  Future<Response> addChecklistWithHttpInfo(AddChecklistRequest addChecklistRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/checklist';

    // ignore: prefer_final_locals
    Object? postBody = addChecklistRequest;

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

  /// Add a new checklist
  ///
  /// Add a new checklist to an existend card
  ///
  /// Parameters:
  ///
  /// * [AddChecklistRequest] addChecklistRequest (required):
  ///   Create a new checklist
  Future<String?> addChecklist(AddChecklistRequest addChecklistRequest,) async {
    final response = await addChecklistWithHttpInfo(addChecklistRequest,);
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

  /// Delete a checklist
  ///
  /// Delete a checklist in an existent card
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   Id of the checklist to delete
  Future<Response> deleteChecklistWithHttpInfo(String checklistId,) async {
    // ignore: prefer_const_declarations
    final path = r'/checklist/{checklistId}'
      .replaceAll('{checklistId}', checklistId);

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

  /// Delete a checklist
  ///
  /// Delete a checklist in an existent card
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   Id of the checklist to delete
  Future<void> deleteChecklist(String checklistId,) async {
    final response = await deleteChecklistWithHttpInfo(checklistId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get checklist by its Id
  ///
  /// Fetch the checklist with all its items
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   ID of board to return
  Future<Response> getChecklistByIdWithHttpInfo(String checklistId,) async {
    // ignore: prefer_const_declarations
    final path = r'/checklist/{checklistId}'
      .replaceAll('{checklistId}', checklistId);

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

  /// Get checklist by its Id
  ///
  /// Fetch the checklist with all its items
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   ID of board to return
  Future<Checklist?> getChecklistById(String checklistId,) async {
    final response = await getChecklistByIdWithHttpInfo(checklistId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Checklist',) as Checklist;
    
    }
    return null;
  }

  /// Update an existent checklist
  ///
  /// Update an existent checklist. Here we should be able to rename the checklist and update its items
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   ID of checklist to return
  ///
  /// * [Checklist] checklist (required):
  ///   Update an existent checklist
  Future<Response> updateChecklistWithHttpInfo(String checklistId, Checklist checklist,) async {
    // ignore: prefer_const_declarations
    final path = r'/checklist/{checklistId}'
      .replaceAll('{checklistId}', checklistId);

    // ignore: prefer_final_locals
    Object? postBody = checklist;

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

  /// Update an existent checklist
  ///
  /// Update an existent checklist. Here we should be able to rename the checklist and update its items
  ///
  /// Parameters:
  ///
  /// * [String] checklistId (required):
  ///   ID of checklist to return
  ///
  /// * [Checklist] checklist (required):
  ///   Update an existent checklist
  Future<void> updateChecklist(String checklistId, Checklist checklist,) async {
    final response = await updateChecklistWithHttpInfo(checklistId, checklist,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
