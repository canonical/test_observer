import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_execution.dart';
import 'artefact_builds.dart';
import 'test_execution_filters.dart';

part 'filtered_test_executions.g.dart';

@riverpod
List<TestExecution> filteredTestExecutions(
  FilteredTestExecutionsRef ref,
  int artefactId,
) {
  final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
  final testExecutions = [
    for (final build in builds)
      for (final testExecution in build.testExecutions) testExecution,
  ];
  final filters = ref.watch(testExecutionFiltersProvider(artefactId));

  return testExecutions
      .filter((testExecution) => filters.doesObjectPassFilters(testExecution))
      .toList();
}
