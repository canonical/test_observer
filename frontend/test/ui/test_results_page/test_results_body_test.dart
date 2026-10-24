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

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/search_page_results.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/search_page_results.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/test_results_page/test_results_body.dart';

import '../../search_page_test_data.dart';

void main() {
  testWidgets('a later-page failure keeps rows visible and offers retry', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final pageFailure = Completer<SearchPageTableResponse>();
    final api = _PagedSearchApi([
      Future.value(
        searchPageResponse(
          count: 2,
          offset: 0,
          rows: [SearchPageTableRow.fromJson(searchPageRowJson(id: 1))],
        ),
      ),
      pageFailure.future,
      Future.value(
        searchPageResponse(
          count: null,
          offset: 1,
          rows: [SearchPageTableRow.fromJson(searchPageRowJson(id: 2))],
        ),
      ),
    ]);
    final filters = const TestResultsFilters(families: ['snap']);
    final scrollController = ScrollController();
    addTearDown(scrollController.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiProvider.overrideWith((ref) => api)],
        child: MaterialApp(
          home: Scaffold(
            body: TestResultsBody(
              filters: filters,
              scrollController: scrollController,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('example-app'), findsOneWidget);

    final container = ProviderScope.containerOf(
      tester.element(find.byType(TestResultsBody)),
    );
    final loadMore = container
        .read(searchPageResultsProvider(filters).notifier)
        .loadMore();
    pageFailure.completeError(Exception('network unavailable'));
    await loadMore;
    await tester.pumpAndSettle();

    expect(find.text('example-app'), findsOneWidget);
    expect(
      find.text('Error loading more results: Exception: network unavailable'),
      findsOneWidget,
    );
    expect(find.text('Retry loading more'), findsOneWidget);

    await tester.tap(find.text('Retry loading more'));
    await tester.pumpAndSettle();

    expect(
      find.text('Error loading more results: Exception: network unavailable'),
      findsNothing,
    );
    expect(
      container
          .read(searchPageResultsProvider(filters))
          .requireValue
          .rows
          .map((row) => row.testResult.id),
      [1, 2],
    );
  });
}

class _PagedSearchApi extends Mock implements ApiRepository {
  _PagedSearchApi(this.responses);

  final List<Future<SearchPageTableResponse>> responses;

  @override
  Future<SearchPageTableResponse> searchTestResultsPage(
    TestResultsFilters filters, {
    required int limit,
    required int offset,
    required bool includeCount,
  }) => responses.removeAt(0);
}
