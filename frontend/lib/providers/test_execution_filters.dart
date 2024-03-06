import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filter.dart';
import '../models/filters.dart';
import '../models/test_execution.dart';
import 'artefact_builds.dart';

part 'test_execution_filters.g.dart';

@riverpod
class TestExecutionFilters extends _$TestExecutionFilters {
  @override
  Filters<TestExecution> build(int artefactId) {
    final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
    final testExecutions = [
      for (final build in builds)
        for (final testExecution in build.testExecutions) testExecution,
    ];

    return Filters<TestExecution>(
      filters: [
        Filter<TestExecution>.fromObjects(
          name: 'Review status',
          extractOption: (te) =>
              te.reviewDecision.isEmpty ? 'Undecided' : 'Reviewed',
          objects: testExecutions,
        ),
        Filter<TestExecution>.fromObjects(
          name: 'Execution status',
          extractOption: (te) => te.status.name,
          objects: testExecutions,
        ),
      ],
    );
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
