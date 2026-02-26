// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/detailed_test_results.dart';
import '../models/test_results_filters.dart';
import 'api.dart';

part 'test_results_search.g.dart';

@riverpod
class TestResultsSearch extends _$TestResultsSearch {
  @override
  AsyncValue<TestResultsSearchResult> build(TestResultsFilters filters) {
    // Automatically load initial data when URI has query params
    if (filters.hasFilters) {
      Future.microtask(() => loadInitial());
    }

    return !filters.hasFilters
        ? AsyncValue.data(TestResultsSearchResult.empty())
        : const AsyncValue.loading();
  }

  // Load initial results when URI changes
  Future<void> loadInitial() async {
    state = const AsyncValue.loading();

    try {
      final result = await _search(limit: 100, offset: 0);
      state = AsyncValue.data(result);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  // Load more results
  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore) return;

    // Keep current data visible while loading
    state = const AsyncValue<TestResultsSearchResult>.loading()
        .copyWithPrevious(state);

    try {
      final results = await _search(
        limit: 100,
        offset: current.testResults.length,
      );

      // Merge results
      final merged = List<TestResultWithContext>.of(current.testResults)
        ..addAll(results.testResults);

      state = AsyncValue.data(
        TestResultsSearchResult(
          count: results.count,
          testResults: merged,
        ),
      );
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<TestResultsSearchResult> _search({
    required int limit,
    required int offset,
  }) async {
    final api = ref.read(apiProvider);
    if (!filters.hasFilters) {
      return TestResultsSearchResult.empty();
    }
    // Update filters with pagination
    final updatedFilters = filters.copyWith(
      limit: limit,
      offset: offset,
    );
    return await api.searchTestResults(updatedFilters);
  }
}
