import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import 'artefact_builds.dart';

part 'filtered_test_execution_ids.g.dart';

@riverpod
Set<int> filteredTestExecutionIds(
  FilteredTestExecutionIdsRef ref,
  int artefactId,
  Uri pageUri,
) {
  final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
  final testExecutions = [
    for (final build in builds)
      for (final testExecution in build.testExecutions) testExecution,
  ];
  final filters =
      emptyTestExecutionFilters.copyWithQueryParams(pageUri.queryParametersAll);

  return testExecutions
      .filter((testExecution) => filters.doesObjectPassFilters(testExecution))
      .map((te) => te.id)
      .toSet();
}
