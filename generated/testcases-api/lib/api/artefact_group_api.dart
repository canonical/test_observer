//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class ArtefactGroupApi {
  ArtefactGroupApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new artefact group
  ///
  /// Add a new artefact group to an existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddArtefactGroupRequest] addArtefactGroupRequest (required):
  ///   Create a new artefact group
  Future<Response> addArtefactGroupWithHttpInfo(AddArtefactGroupRequest addArtefactGroupRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact_group';

    // ignore: prefer_final_locals
    Object? postBody = addArtefactGroupRequest;

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

  /// Add a new artefact group
  ///
  /// Add a new artefact group to an existing lane. With this method we should be able to create an empty open artefact without any environmentss, comments and labels. The response should consist of new artefact Id
  ///
  /// Parameters:
  ///
  /// * [AddArtefactGroupRequest] addArtefactGroupRequest (required):
  ///   Create a new artefact group
  Future<String?> addArtefactGroup(AddArtefactGroupRequest addArtefactGroupRequest,) async {
    final response = await addArtefactGroupWithHttpInfo(addArtefactGroupRequest,);
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

  /// Get environments for artefact group
  ///
  /// Fetch the JSON representation of the environments in a artefact
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] artefactGroupId (required):
  ///   Id of the artefact
  Future<Response> getenvironmentssInArtefactWithHttpInfo(String artefactGroupId,) async {
    // ignore: prefer_const_declarations
    final path = r'/artefact_group/{artefactGroupId}/environments'
      .replaceAll('{artefactGroupId}', artefactGroupId);

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

  /// Get environments for artefact group
  ///
  /// Fetch the JSON representation of the environments in a artefact
  ///
  /// Parameters:
  ///
  /// * [String] artefactGroupId (required):
  ///   Id of the artefact
  Future<List<Environments>?> getenvironmentssInArtefact(String artefactGroupId,) async {
    final response = await getenvironmentssInArtefactWithHttpInfo(artefactGroupId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Environments>') as List)
        .cast<Environments>()
        .toList();

    }
    return null;
  }
}
