//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class EnvironmentsApi {
  EnvironmentsApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new environments
  ///
  /// Add a new environments to an existend artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddenvironmentsRequest] addenvironmentsRequest (required):
  ///   Create a new environments
  Future<Response> addenvironmentsWithHttpInfo(AddenvironmentsRequest addenvironmentsRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/environments';

    // ignore: prefer_final_locals
    Object? postBody = addenvironmentsRequest;

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

  /// Add a new environments
  ///
  /// Add a new environments to an existend artefact
  ///
  /// Parameters:
  ///
  /// * [AddenvironmentsRequest] addenvironmentsRequest (required):
  ///   Create a new environments
  Future<String?> addenvironments(AddenvironmentsRequest addenvironmentsRequest,) async {
    final response = await addenvironmentsWithHttpInfo(addenvironmentsRequest,);
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

  /// Delete a environments
  ///
  /// Delete a environments in an existent artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   Id of the environments to delete
  Future<Response> deleteenvironmentsWithHttpInfo(String environmentsId,) async {
    // ignore: prefer_const_declarations
    final path = r'/environments/{environmentsId}'
      .replaceAll('{environmentsId}', environmentsId);

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

  /// Delete a environments
  ///
  /// Delete a environments in an existent artefact
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   Id of the environments to delete
  Future<void> deleteenvironments(String environmentsId,) async {
    final response = await deleteenvironmentsWithHttpInfo(environmentsId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get environments by its Id
  ///
  /// Fetch the environments with all its items
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   ID of page to return
  Future<Response> getenvironmentsByIdWithHttpInfo(String environmentsId,) async {
    // ignore: prefer_const_declarations
    final path = r'/environments/{environmentsId}'
      .replaceAll('{environmentsId}', environmentsId);

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

  /// Get environments by its Id
  ///
  /// Fetch the environments with all its items
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   ID of page to return
  Future<Environments?> getenvironmentsById(String environmentsId,) async {
    final response = await getenvironmentsByIdWithHttpInfo(environmentsId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Environments',) as Environments;
    
    }
    return null;
  }

  /// Update an existent environments
  ///
  /// Update an existent environments. Here we should be able to rename the environments and update its items
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   ID of environments to return
  ///
  /// * [Environments] environments (required):
  ///   Update an existent environments
  Future<Response> updateenvironmentsWithHttpInfo(String environmentsId, Environments environments,) async {
    // ignore: prefer_const_declarations
    final path = r'/environments/{environmentsId}'
      .replaceAll('{environmentsId}', environmentsId);

    // ignore: prefer_final_locals
    Object? postBody = environments;

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

  /// Update an existent environments
  ///
  /// Update an existent environments. Here we should be able to rename the environments and update its items
  ///
  /// Parameters:
  ///
  /// * [String] environmentsId (required):
  ///   ID of environments to return
  ///
  /// * [Environments] environments (required):
  ///   Update an existent environments
  Future<void> updateenvironments(String environmentsId, Environments environments,) async {
    final response = await updateenvironmentsWithHttpInfo(environmentsId, environments,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
