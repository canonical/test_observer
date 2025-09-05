// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/detailed_test_results.dart';
import 'api.dart';

part 'test_results_search.g.dart';

@riverpod
class TestResultsSearchFromUri extends _$TestResultsSearchFromUri {
  @override
  AsyncValue<TestResultsSearchResult> build(Uri pageUri) {
    // Automatically load initial data when URI has query params
    if (pageUri.queryParametersAll.isNotEmpty) {
      Future.microtask(() => loadInitial());
    }

    return pageUri.queryParametersAll.isEmpty
        ? AsyncValue.data(TestResultsSearchResult.empty())
        : const AsyncValue.loading();
  }

  // Load initial results when URI changes
  Future<void> loadInitial() async {
    state = const AsyncValue.loading();

    try {
      final result = await _searchWithUri(limit: 100, offset: 0);
      state = AsyncValue.data(result);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  // Load more results (pagination)
  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore) return;

    // Keep current data visible while loading
    state = const AsyncValue<TestResultsSearchResult>.loading()
        .copyWithPrevious(state);

    try {
      final result = await _searchWithUri(
        limit: 100,
        offset: current.testResults.length,
      );

      // Merge results
      final merged = List<TestResultWithContext>.of(current.testResults)
        ..addAll(result.testResults);

      state = AsyncValue.data(
        TestResultsSearchResult(
          count: result.count,
          testResults: merged,
        ),
      );
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<TestResultsSearchResult> _searchWithUri({
    required int limit,
    required int offset,
  }) async {
    final api = ref.read(apiProvider);
    final parameters = pageUri.queryParametersAll;

    // Parse URI parameters directly (no dependency on other providers)
    final familiesValues = parameters['families'] ?? [];
    final families = familiesValues.isNotEmpty
        ? familiesValues.first.split(',').map((f) => f.toLowerCase()).toList()
        : <String>[];

    final environmentsValues = parameters['environments'] ?? [];
    final environments = environmentsValues.isNotEmpty
        ? environmentsValues.first.split(',').toList()
        : <String>[];

    final testCasesValues = parameters['test_cases'] ?? [];
    final testCases = testCasesValues.isNotEmpty
        ? testCasesValues.first.split(',').toList()
        : <String>[];

    // Only search if we have filters
    if (families.isEmpty && environments.isEmpty && testCases.isEmpty) {
      return TestResultsSearchResult.empty();
    }

    return await api.searchTestResults(
      families: families.isNotEmpty ? families : null,
      environments: environments.isNotEmpty ? environments : null,
      testCases: testCases.isNotEmpty ? testCases : null,
      limit: limit,
      offset: offset,
    );
  }
}
