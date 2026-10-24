// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../search_page_test_data.dart';

void main() {
  test('uses page-specific endpoints and count query parameters', () async {
    final adapter = _RecordingAdapter();
    final repository = ApiRepository(
      dio: Dio(BaseOptions(baseUrl: 'https://test-observer.invalid'))
        ..httpClientAdapter = adapter,
    );
    final filters = const TestResultsFilters(
      families: ['snap'],
      testCases: ['suite/case'],
    );

    await repository.searchTestResultsPage(
      filters,
      limit: 100,
      offset: 0,
      includeCount: true,
    );
    await repository.searchTestResultsPage(
      filters,
      limit: 100,
      offset: 100,
      includeCount: false,
    );
    await repository.getSearchPageTestResultDetails(23);

    expect(adapter.requests.map((request) => request.path), [
      '/v1/test-results/search-page',
      '/v1/test-results/search-page',
      '/v1/test-results/search-page/23',
    ]);
    expect(adapter.requests[0].queryParameters['include_count'], isTrue);
    expect(adapter.requests[0].queryParameters['offset'], ['0']);
    expect(adapter.requests[0].queryParameters['limit'], ['100']);
    expect(adapter.requests[0].queryParameters['families'], ['snap']);
    expect(adapter.requests[0].queryParameters['test_cases'], ['suite/case']);
    expect(adapter.requests[1].queryParameters['include_count'], isFalse);
    expect(adapter.requests[1].queryParameters['offset'], ['100']);
    expect(adapter.requests[2].queryParameters, isEmpty);
  });

  test(
    'legacy searchTestResults remains on the full results endpoint',
    () async {
      final adapter = _RecordingAdapter();
      final repository = ApiRepository(
        dio: Dio(BaseOptions(baseUrl: 'https://test-observer.invalid'))
          ..httpClientAdapter = adapter,
      );

      final response = await repository.searchTestResults(
        const TestResultsFilters(families: ['snap']),
      );

      expect(response.count, 0);
      expect(adapter.requests.single.path, '/v1/test-results');
      expect(adapter.requests.single.queryParameters['families'], ['snap']);
      expect(
        adapter.requests.single.queryParameters,
        isNot(contains('include_count')),
      );
    },
  );
}

class _RecordingAdapter implements HttpClientAdapter {
  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final Map<String, dynamic> response;
    if (options.path.endsWith('/23')) {
      response = searchPageDetailsJson();
    } else if (options.path.endsWith('/search-page')) {
      response = {
        'count': options.queryParameters['include_count'] == true ? 42 : null,
        'limit': 100,
        'offset': 0,
        'rows': [searchPageRowJson()],
      };
    } else {
      response = {'count': 0, 'test_results': []};
    }
    return ResponseBody.fromString(
      jsonEncode(response),
      200,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
