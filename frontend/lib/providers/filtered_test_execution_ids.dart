import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'artefact_builds.dart';
import 'test_execution_filters.dart';

part 'filtered_test_execution_ids.g.dart';

@riverpod
Set<int> filteredTestExecutionIds(
  FilteredTestExecutionIdsRef ref,
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
      .map((te) => te.id)
      .toSet();
}
