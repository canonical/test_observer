//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class LaneApi {
  LaneApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new lane
  ///
  /// Add a new lane to an existent page. This method should create an empty open lane and return the new lane Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddLaneRequest] addLaneRequest (required):
  ///   Create a new lane
  Future<Response> addLaneWithHttpInfo(AddLaneRequest addLaneRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/lane';

    // ignore: prefer_final_locals
    Object? postBody = addLaneRequest;

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

  /// Add a new lane
  ///
  /// Add a new lane to an existent page. This method should create an empty open lane and return the new lane Id
  ///
  /// Parameters:
  ///
  /// * [AddLaneRequest] addLaneRequest (required):
  ///   Create a new lane
  Future<String?> addLane(AddLaneRequest addLaneRequest,) async {
    final response = await addLaneWithHttpInfo(addLaneRequest,);
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

  /// Delete a lane
  ///
  /// Permanently delete a lane from the page and all artefacts in this lane
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   lane id to delete
  Future<Response> deleteLaneWithHttpInfo(String laneId,) async {
    // ignore: prefer_const_declarations
    final path = r'/lane/{laneId}'
      .replaceAll('{laneId}', laneId);

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

  /// Delete a lane
  ///
  /// Permanently delete a lane from the page and all artefacts in this lane
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   lane id to delete
  Future<void> deleteLane(String laneId,) async {
    final response = await deleteLaneWithHttpInfo(laneId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get all artefacts in the lane
  ///
  /// With this method we should be able to fetch all the artefacts (in JSON) from the lane
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   lane id to search artefacts in
  Future<Response> getArtefactsInLaneWithHttpInfo(String laneId,) async {
    // ignore: prefer_const_declarations
    final path = r'/lane/{laneId}/artefacts'
      .replaceAll('{laneId}', laneId);

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

  /// Get all artefacts in the lane
  ///
  /// With this method we should be able to fetch all the artefacts (in JSON) from the lane
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   lane id to search artefacts in
  Future<List<Artefact>?> getArtefactsInLane(String laneId,) async {
    final response = await getArtefactsInLaneWithHttpInfo(laneId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Artefact>') as List)
        .cast<Artefact>()
        .toList();

    }
    return null;
  }

  /// Get JSON representation of the lane by its Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   ID of page to return
  Future<Response> getLaneByIdWithHttpInfo(String laneId,) async {
    // ignore: prefer_const_declarations
    final path = r'/lane/{laneId}'
      .replaceAll('{laneId}', laneId);

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

  /// Get JSON representation of the lane by its Id
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   ID of page to return
  Future<Lane?> getLaneById(String laneId,) async {
    final response = await getLaneByIdWithHttpInfo(laneId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Lane',) as Lane;
    
    }
    return null;
  }

  /// Update an existent lane
  ///
  /// With this method we should be able move lane to another page (by updating pageId), chage its name and status (maybe also Id itself). If we close a lane, the artefacts in it should also be closed
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   ID of lane to return
  ///
  /// * [Lane] lane (required):
  ///   Update an existent lane
  Future<Response> updateLaneWithHttpInfo(String laneId, Lane lane,) async {
    // ignore: prefer_const_declarations
    final path = r'/lane/{laneId}'
      .replaceAll('{laneId}', laneId);

    // ignore: prefer_final_locals
    Object? postBody = lane;

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

  /// Update an existent lane
  ///
  /// With this method we should be able move lane to another page (by updating pageId), chage its name and status (maybe also Id itself). If we close a lane, the artefacts in it should also be closed
  ///
  /// Parameters:
  ///
  /// * [String] laneId (required):
  ///   ID of lane to return
  ///
  /// * [Lane] lane (required):
  ///   Update an existent lane
  Future<void> updateLane(String laneId, Lane lane,) async {
    final response = await updateLaneWithHttpInfo(laneId, lane,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
