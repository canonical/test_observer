import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import '../models/test_execution.dart';
import 'artefact_builds.dart';

part 'test_execution_filters.g.dart';

@riverpod
class TestExecutionFilters extends _$TestExecutionFilters {
  @override
  Filters<TestExecution> build(int artefactId, Uri pageUri) {
    final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
    final testExecutions = [
      for (final build in builds)
        for (final testExecution in build.testExecutions) testExecution,
    ];

    return emptyTestExecutionFilters
        .copyWithOptionsExtracted(testExecutions)
        .copyWithQueryParams(pageUri.queryParametersAll);
  }

  void handleFilterOptionChange(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    state = state.copyWithFilterOptionValue(
      filterName,
      optionName,
      optionValue,
    );
  }
}
