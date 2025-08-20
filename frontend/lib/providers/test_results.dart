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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_result.dart';
import 'api.dart';

part 'test_results.g.dart';

@riverpod
Future<List<TestResult>> testResults(Ref ref, int testExecutionId) async {
  final api = ref.watch(apiProvider);
  return await api.getTestExecutionResults(testExecutionId);
}

final familySelectionsProvider = StateProvider<Map<String, bool>>((ref) => {
      'snap': false,
      'deb': false,
      'charm': false,
      'image': false,
    });

final environmentsProvider = FutureProvider<List<String>>((ref) async {
  final api = ref.read(apiProvider);
  return api.getEnvironments();
});

final testCasesProvider = FutureProvider<List<String>>((ref) async {
  final api = ref.read(apiProvider);
  return api.getTestCases();
});

final selectedEnvironmentsProvider = StateProvider<Set<String>>((ref) => {});
final selectedTestCasesProvider = StateProvider<Set<String>>((ref) => {});

// Notifier for managing test results search
final testResultsSearchNotifierProvider = StateNotifierProvider<
    TestResultsSearchNotifier, AsyncValue<Map<String, dynamic>>>(
  (ref) => TestResultsSearchNotifier(ref),
);

class TestResultsSearchNotifier
    extends StateNotifier<AsyncValue<Map<String, dynamic>>> {
  TestResultsSearchNotifier(this.ref)
      : super(const AsyncValue.data({'count': 0, 'test_results': []}));

  final Ref ref;

  Future<void> search({int limit = 500, int offset = 0}) async {
    state = const AsyncValue.loading();

    try {
      final api = ref.read(apiProvider);

      final selectedFamilies = ref.read(familySelectionsProvider);
      final selectedEnvironments = ref.read(selectedEnvironmentsProvider);
      final selectedTestCases = ref.read(selectedTestCasesProvider);

      final families = selectedFamilies.entries
          .where((entry) => entry.value)
          .map((entry) => entry.key.toLowerCase())
          .toList();

      final environments = selectedEnvironments.toList();
      final testCases = selectedTestCases.toList();

      final result = await api.searchTestResults(
        families: families.isNotEmpty ? families : null,
        environments: environments.isNotEmpty ? environments : null,
        testCases: testCases.isNotEmpty ? testCases : null,
        limit: limit,
        offset: offset,
      );

      state = AsyncValue.data(result);
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  void reset() {
    state = const AsyncValue.data({'count': 0, 'test_results': []});
  }
}
