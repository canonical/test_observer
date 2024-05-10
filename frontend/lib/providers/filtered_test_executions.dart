import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import 'artefact_builds.dart';

import '../models/test_execution.dart';
import '../routing.dart';

part 'filtered_test_executions.g.dart';

@riverpod
List<TestExecution> filteredTestExecutions(
  FilteredTestExecutionsRef ref,
  Uri pageUri,
) {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final filters =
      emptyTestExecutionFilters.copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue = pageUri.queryParameters['q'] ?? '';

  final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
  final testExecutions = [
    for (final build in builds)
      for (final testExecution in build.testExecutions) testExecution,
  ];

  return testExecutions
      .filter(
        (testExecution) =>
            _testExecutionPassesSearch(testExecution, searchValue) &&
            filters.doesObjectPassFilters(testExecution),
      )
      .toList();
}

bool _testExecutionPassesSearch(
  TestExecution testExecution,
  String searchValue,
) {
  return testExecution.environment.name
      .toLowerCase()
      .contains(searchValue.toLowerCase());
}
