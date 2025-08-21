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
import 'api.dart';
import 'test_results_filters.dart';

part 'test_results_search.g.dart';

@riverpod
class TestResultsSearch extends _$TestResultsSearch {
  @override
  AsyncValue<TestResultsSearchResult> build() {
    return const AsyncValue.data(TestResultsSearchResult.empty());
  }

  Future<void> search({int limit = 500, int offset = 0}) async {
    if (offset > 0 && state.hasValue) {
      state = const AsyncValue<TestResultsSearchResult>.loading()
          .copyWithPrevious(state);
    } else {
      state = const AsyncValue.loading();
    }

    try {
      final api = ref.read(apiProvider);
      final filters = ref.read(testResultsFiltersProvider);

      final families = filters.familySelections.entries
          .where((entry) => entry.value)
          .map((entry) => entry.key.toLowerCase())
          .toList();

      final environments = filters.selectedEnvironments.toList();
      final testCases = filters.selectedTestCases.toList();

      final result = await api.searchTestResults(
        families: families.isNotEmpty ? families : null,
        environments: environments.isNotEmpty ? environments : null,
        testCases: testCases.isNotEmpty ? testCases : null,
        limit: limit,
        offset: offset,
      );

      final searchResult = TestResultsSearchResult(
        count: result['count'] as int,
        testResults: (result['test_results'] as List<dynamic>)
            .cast<Map<String, dynamic>>(),
        hasMore: result['count'] > offset + limit,
      );

      if (offset > 0 && state.hasValue) {
        final currentData = state.value!;
        final mergedResults = [
          ...currentData.testResults,
          ...searchResult.testResults,
        ];
        state =
            AsyncValue.data(searchResult.copyWith(testResults: mergedResults));
      } else {
        state = AsyncValue.data(searchResult);
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> loadMore() async {
    if (!state.hasValue || !state.value!.hasMore) return;

    final currentData = state.value!;
    await search(
      limit: 500,
      offset: currentData.testResults.length,
    );
  }
}

class TestResultsSearchResult {
  final int count;
  final List<Map<String, dynamic>> testResults;
  final bool hasMore;

  const TestResultsSearchResult({
    required this.count,
    required this.testResults,
    required this.hasMore,
  });

  const TestResultsSearchResult.empty()
      : count = 0,
        testResults = const [],
        hasMore = false;

  TestResultsSearchResult copyWith({
    int? count,
    List<Map<String, dynamic>>? testResults,
    bool? hasMore,
  }) {
    return TestResultsSearchResult(
      count: count ?? this.count,
      testResults: testResults ?? this.testResults,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}
