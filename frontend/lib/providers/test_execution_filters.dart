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

    decisionExtractor(TestExecution te) =>
        te.reviewDecision.isEmpty ? 'Undecided' : 'Reviewed';
    statusExtractor(TestExecution te) => te.status.name;

    final decisionOptions = <String>{};
    final statusOptions = <String>{};
    for (final te in testExecutions) {
      decisionOptions.add(decisionExtractor(te));
      statusOptions.add(statusExtractor(te));
    }

    return Filters<TestExecution>(
      filters: [
        Filter<TestExecution>(
          name: 'Review status',
          extractOption: decisionExtractor,
          availableOptions: decisionOptions.toList()..sort(),
        ),
        Filter<TestExecution>(
          name: 'Execution status',
          extractOption: statusExtractor,
          availableOptions: statusOptions.toList()..sort(),
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
