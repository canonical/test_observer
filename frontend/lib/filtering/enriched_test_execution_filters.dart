import 'package:dartx/dartx.dart';

import '../models/enriched_test_execution.dart';
import 'multi_select_filter.dart';

final testPlanNameFilter = MultiSelectFilter(
  name: 'Test Plan',
  extractOptions: (List<EnrichedTestExecution> enrichedExecutions) =>
      enrichedExecutions.map((ee) => ee.testExecution.testPlan).toSet(),
  filter: (
    List<EnrichedTestExecution> enrichedExecutions,
    Set<String> names,
  ) =>
      enrichedExecutions
          .filter((ee) => names.contains(ee.testExecution.testPlan))
          .toList(),
);

final enrichedTestExecutionFilters = [
  testPlanNameFilter,
];
