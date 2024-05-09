import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'artefact_builds.dart';

import '../models/test_execution.dart';
import '../routing.dart';
import 'filtered_test_execution_ids.dart';

part 'filtered_test_executions.g.dart';

@riverpod
List<TestExecution> filteredTestExecutions(
    FilteredTestExecutionsRef ref, Uri pageUri) {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
  final filteredTestExecutionIds =
      ref.watch(filteredTestExecutionIdsProvider(pageUri));
  return [
    for (final build in builds)
      for (final te in build.testExecutions)
        if (filteredTestExecutionIds.contains(te.id)) te,
  ];
}
