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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/search_page_results.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/search_page_results.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../search_page_test_data.dart';
import '../utilities.dart';

void main() {
  test(
    'requests count once, pages by current length, and retains exact count',
    () async {
      final api = _SearchPageApiFake((offset, includeCount, filters) {
        if (offset == 0) {
          return searchPageResponse(
            count: includeCount ? 250 : null,
            offset: offset,
            rows: [
              SearchPageTableRow.fromJson(searchPageRowJson(id: 1)),
              SearchPageTableRow.fromJson(searchPageRowJson(id: 2)),
            ],
          );
        }
        return searchPageResponse(
          count: null,
          offset: offset,
          rows: [SearchPageTableRow.fromJson(searchPageRowJson(id: 3))],
        );
      });
      final filters = const TestResultsFilters(families: ['snap']);
      final container = createContainer(
        overrides: [apiProvider.overrideWith((ref) => api)],
      );
      container.listen(searchPageResultsProvider(filters), (_, __) {});
      await Future<void>.delayed(Duration.zero);

      final notifier = container.read(
        searchPageResultsProvider(filters).notifier,
      );
      expect(
        container.read(searchPageResultsProvider(filters)).requireValue.count,
        250,
      );
      await notifier.loadMore();

      final loaded =
          container.read(searchPageResultsProvider(filters)).requireValue;
      expect(loaded.count, 250);
      expect(loaded.rows.map((row) => row.testResult.id), [1, 2, 3]);
      expect(api.calls.map((call) => call.offset), [0, 2]);
      expect(api.calls.map((call) => call.includeCount), [true, false]);
      expect(api.calls.every((call) => call.filters == filters), isTrue);
    },
  );

  test(
    'a replacement filter starts at offset zero with a fresh exact count',
    () async {
      final api = _SearchPageApiFake((offset, includeCount, filters) {
        return searchPageResponse(
          count: includeCount
              ? (filters.families.single == 'snap' ? 250 : 4)
              : null,
          offset: offset,
          rows: [],
        );
      });
      final firstFilters = const TestResultsFilters(families: ['snap']);
      final replacementFilters = const TestResultsFilters(families: ['deb']);
      final container = createContainer(
        overrides: [apiProvider.overrideWith((ref) => api)],
      );
      container.listen(searchPageResultsProvider(firstFilters), (_, __) {});
      await Future<void>.delayed(Duration.zero);
      expect(
        container
            .read(searchPageResultsProvider(firstFilters))
            .requireValue
            .count,
        250,
      );

      container.listen(
        searchPageResultsProvider(replacementFilters),
        (_, __) {},
      );
      await Future<void>.delayed(Duration.zero);

      expect(
        container
            .read(searchPageResultsProvider(replacementFilters))
            .requireValue
            .count,
        4,
      );
      expect(api.calls.map((call) => call.offset), [0, 0]);
      expect(api.calls.map((call) => call.includeCount), [true, true]);
      expect(api.calls.map((call) => call.filters.families.single), [
        'snap',
        'deb',
      ]);
    },
  );

  test('a later-page error preserves rows and can be retried', () async {
    var laterPageCalls = 0;
    final api = _SearchPageApiFake((offset, includeCount, filters) {
      if (offset == 0) {
        return searchPageResponse(
          count: includeCount ? 3 : null,
          offset: offset,
          rows: [SearchPageTableRow.fromJson(searchPageRowJson(id: 1))],
        );
      }
      laterPageCalls++;
      if (laterPageCalls == 1) throw Exception('network unavailable');
      return searchPageResponse(
        count: null,
        offset: offset,
        rows: [SearchPageTableRow.fromJson(searchPageRowJson(id: 2))],
      );
    });
    final filters = const TestResultsFilters(families: ['snap']);
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => api)],
    );
    container.listen(searchPageResultsProvider(filters), (_, __) {});
    await Future<void>.delayed(Duration.zero);

    final notifier = container.read(
      searchPageResultsProvider(filters).notifier,
    );
    await notifier.loadMore();

    final failedPage = container.read(searchPageResultsProvider(filters));
    expect(failedPage.hasError, isTrue);
    expect(
      failedPage.valueOrNull?.rows.map((row) => row.testResult.id),
      [1],
    );

    await notifier.loadMore();

    final retriedPage = container.read(searchPageResultsProvider(filters));
    expect(retriedPage.hasError, isFalse);
    expect(
      retriedPage.requireValue.rows.map((row) => row.testResult.id),
      [1, 2],
    );
    expect(api.calls.map((call) => call.offset), [0, 1, 1]);
  });
}

class _SearchPageApiFake extends Mock implements ApiRepository {
  _SearchPageApiFake(this.respond);

  final SearchPageTableResponse Function(
    int offset,
    bool includeCount,
    TestResultsFilters filters,
  ) respond;

  final calls =
      <({TestResultsFilters filters, int offset, bool includeCount})>[];

  @override
  Future<SearchPageTableResponse> searchTestResultsPage(
    TestResultsFilters filters, {
    required int limit,
    required int offset,
    required bool includeCount,
  }) async {
    calls.add((filters: filters, offset: offset, includeCount: includeCount));
    return respond(offset, includeCount, filters);
  }
}
