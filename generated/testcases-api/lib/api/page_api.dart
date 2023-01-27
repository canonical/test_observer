//
// AUTO-GENERATED FILE, DO NOT MODIFY!
//
// @dart=2.12

// ignore_for_file: unused_element, unused_import
// ignore_for_file: always_put_required_named_parameters_first
// ignore_for_file: constant_identifier_names
// ignore_for_file: lines_longer_than_80_chars

part of openapi.api;


class PageApi {
  PageApi([ApiClient? apiClient]) : apiClient = apiClient ?? defaultApiClient;

  final ApiClient apiClient;

  /// Add a new page of build artefacts
  ///
  /// Create a new page. Here we specify the page name, the status of the page is open. The response should contian of page ID
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [AddPageRequest] addPageRequest (required):
  ///   A new page description
  Future<Response> addPageWithHttpInfo(AddPageRequest addPageRequest,) async {
    // ignore: prefer_const_declarations
    final path = r'/page';

    // ignore: prefer_final_locals
    Object? postBody = addPageRequest;

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

  /// Add a new page of build artefacts
  ///
  /// Create a new page. Here we specify the page name, the status of the page is open. The response should contian of page ID
  ///
  /// Parameters:
  ///
  /// * [AddPageRequest] addPageRequest (required):
  ///   A new page description
  Future<String?> addPage(AddPageRequest addPageRequest,) async {
    final response = await addPageWithHttpInfo(addPageRequest,);
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

  /// Delete a page
  ///
  /// Permanently delete an existing page
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   page Id to delete
  Future<Response> deletePageWithHttpInfo(String pageId,) async {
    // ignore: prefer_const_declarations
    final path = r'/page/{pageId}'
      .replaceAll('{pageId}', pageId);

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

  /// Delete a page
  ///
  /// Permanently delete an existing page
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   page Id to delete
  Future<void> deletePage(String pageId,) async {
    final response = await deletePageWithHttpInfo(pageId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }

  /// Get all artefacts on the page
  ///
  /// Returns an array of artefacts on the page
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<Response> getArtefactsOnPageWithHttpInfo(String pageId,) async {
    // ignore: prefer_const_declarations
    final path = r'/page/{pageId}/artefacts'
      .replaceAll('{pageId}', pageId);

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

  /// Get all artefacts on the page
  ///
  /// Returns an array of artefacts on the page
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<List<Artefact>?> getArtefactsOnPage(String pageId,) async {
    final response = await getArtefactsOnPageWithHttpInfo(pageId,);
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

  /// Get all lanes on the page
  ///
  /// Returns an array of lanes on the page
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<Response> getLanesOnPageWithHttpInfo(String pageId,) async {
    // ignore: prefer_const_declarations
    final path = r'/page/{pageId}/lanes'
      .replaceAll('{pageId}', pageId);

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

  /// Get all lanes on the page
  ///
  /// Returns an array of lanes on the page
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<List<Lane>?> getLanesOnPage(String pageId,) async {
    final response = await getLanesOnPageWithHttpInfo(pageId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      final responseBody = await _decodeBodyBytes(response);
      return (await apiClient.deserializeAsync(responseBody, 'List<Lane>') as List)
        .cast<Lane>()
        .toList();

    }
    return null;
  }

  /// Fetch a page by ID
  ///
  /// Returns a single page JSON representation
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<Response> getPageByIdWithHttpInfo(String pageId,) async {
    // ignore: prefer_const_declarations
    final path = r'/page/{pageId}'
      .replaceAll('{pageId}', pageId);

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

  /// Fetch a page by ID
  ///
  /// Returns a single page JSON representation
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  Future<Page?> getPageById(String pageId,) async {
    final response = await getPageByIdWithHttpInfo(pageId,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
    // When a remote server returns no body with a status of 204, we shall not decode it.
    // At the time of writing this, `dart:convert` will throw an "Unexpected end of input"
    // FormatException when trying to decode an empty string.
    if (response.body.isNotEmpty && response.statusCode != HttpStatus.noContent) {
      return await apiClient.deserializeAsync(await _decodeBodyBytes(response), 'Page',) as Page;
    
    }
    return null;
  }

  /// Update an existent page
  ///
  /// With this method we should be able to update page name and status (and maybe id). If we close the page here, the artefacts and lanes on it should also be closed
  ///
  /// Note: This method returns the HTTP [Response].
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  ///
  /// * [Page] page (required):
  ///   Update an existent page
  Future<Response> updatePageWithHttpInfo(String pageId, Page page,) async {
    // ignore: prefer_const_declarations
    final path = r'/page/{pageId}'
      .replaceAll('{pageId}', pageId);

    // ignore: prefer_final_locals
    Object? postBody = page;

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

  /// Update an existent page
  ///
  /// With this method we should be able to update page name and status (and maybe id). If we close the page here, the artefacts and lanes on it should also be closed
  ///
  /// Parameters:
  ///
  /// * [String] pageId (required):
  ///   ID of page to return
  ///
  /// * [Page] page (required):
  ///   Update an existent page
  Future<void> updatePage(String pageId, Page page,) async {
    final response = await updatePageWithHttpInfo(pageId, page,);
    if (response.statusCode >= HttpStatus.badRequest) {
      throw ApiException(response.statusCode, await _decodeBodyBytes(response));
    }
  }
}
