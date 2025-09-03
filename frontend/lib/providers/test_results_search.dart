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
import 'test_results_filters.dart';

part 'test_results_search.g.dart';

@riverpod
class TestResultsSearch extends _$TestResultsSearch {
  @override
  AsyncValue<TestResultsSearchResult> build() {
    return AsyncValue.data(TestResultsSearchResult.empty());
  }

  Future<void> search({int limit = 100, int offset = 0}) async {
    // Keep existing data visible while loading more
    if (offset > 0 && state.hasValue) {
      state = const AsyncValue<TestResultsSearchResult>.loading()
          .copyWithPrevious(state);
    } else {
      state = const AsyncValue.loading();
    }

    final api = ref.read(apiProvider);
    final filters = ref.read(testResultsFiltersProvider);

    final families =
        filters.selectedFamilies.map((f) => f.toLowerCase()).toList();
    final environments = filters.selectedEnvironments.toList();
    final testCases = filters.selectedTestCases.toList();

    final result = await api.searchTestResults(
      families: families.isNotEmpty ? families : null,
      environments: environments.isNotEmpty ? environments : null,
      testCases: testCases.isNotEmpty ? testCases : null,
      limit: limit,
      offset: offset,
    );

    if (offset > 0 && state.hasValue) {
      final current = state.value!;
      final merged = List<TestResultWithContext>.of(current.testResults)
        ..addAll(result.testResults);

      state = AsyncValue.data(
        TestResultsSearchResult(
          count: result.count,
          testResults: merged,
        ),
      );
    } else {
      state = AsyncValue.data(result);
    }
  }

  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore) return;

    await search(limit: 100, offset: current.testResults.length);
  }
}
