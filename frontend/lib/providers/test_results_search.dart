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

import 'package:flutter/foundation.dart' show compute;
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/detailed_test_results.dart';
import '../models/test_result.dart';
import '../models/test_execution.dart';
import '../models/artefact.dart';

import 'api.dart';
import 'test_results_filters.dart';

part 'test_results_search.g.dart';

/// Top-level parsing

class _ParsedSearchPage {
  final int count;
  final List<TestResultWithContext> items;
  const _ParsedSearchPage({required this.count, required this.items});
}

_ParsedSearchPage _parseSearchResults(Map<String, dynamic> result) {
  final list = (result['test_results'] as List).cast<Map<String, dynamic>>();

  final items = List<TestResultWithContext>.generate(list.length, (i) {
    final m = list[i];

    final testResult =
        TestResult.fromJson(m['test_result'] as Map<String, dynamic>);
    final testExecution =
        TestExecution.fromJson(m['test_execution'] as Map<String, dynamic>);
    final artefact = Artefact.fromJson(m['artefact'] as Map<String, dynamic>);
    final artefactBuild = ArtefactBuildMinimal.fromJson(
      m['artefact_build'] as Map<String, dynamic>,
    );

    return TestResultWithContext(
      testResult: testResult,
      testExecution: testExecution,
      artefact: artefact,
      artefactBuild: artefactBuild,
    );
  });

  return _ParsedSearchPage(
    count: result['count'] as int,
    items: items,
  );
}

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

    try {
      final api = ref.read(apiProvider);
      final filters = ref.read(testResultsFiltersProvider);

      final families =
          filters.familySelections.map((f) => f.toLowerCase()).toList();
      final environments = filters.selectedEnvironments.toList();
      final testCases = filters.selectedTestCases.toList();

      final raw = await api.searchTestResults(
        families: families.isNotEmpty ? families : null,
        environments: environments.isNotEmpty ? environments : null,
        testCases: testCases.isNotEmpty ? testCases : null,
        limit: limit,
        offset: offset,
      );

      final parsed = await compute(_parseSearchResults, raw);
      final hasMore = parsed.count > offset + limit;

      if (offset > 0 && state.hasValue) {
        final current = state.value!;
        final merged = List<TestResultWithContext>.of(current.testResults)
          ..addAll(parsed.items);

        state = AsyncValue.data(
          TestResultsSearchResult(
            count: parsed.count,
            testResults: merged,
            hasMore: hasMore,
          ),
        );
      } else {
        state = AsyncValue.data(
          TestResultsSearchResult(
            count: parsed.count,
            testResults: parsed.items,
            hasMore: hasMore,
          ),
        );
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (current == null || !current.hasMore) return;

    await search(limit: 100, offset: current.testResults.length);
  }
}
