import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import '../models/test_execution.dart';
import '../routing.dart';
import 'artefact_builds.dart';

part 'filtered_test_execution_ids.g.dart';

@riverpod
Set<int> filteredTestExecutionIds(
  FilteredTestExecutionIdsRef ref,
  Uri pageUri,
) {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
  final testExecutions = [
    for (final build in builds)
      for (final testExecution in build.testExecutions) testExecution,
  ];
  final filters =
      emptyTestExecutionFilters.copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue = pageUri.queryParameters['q'] ?? '';

  return testExecutions
      .filter(
        (testExecution) =>
            _testExecutionPassesSearch(testExecution, searchValue) &&
            filters.doesObjectPassFilters(testExecution),
      )
      .map((te) => te.id)
      .toSet();
}

bool _testExecutionPassesSearch(
  TestExecution testExecution,
  String searchValue,
) {
  return testExecution.environment.name
      .toLowerCase()
      .contains(searchValue.toLowerCase());
}
