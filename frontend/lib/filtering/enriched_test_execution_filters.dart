import '../models/enriched_test_execution.dart';
import 'multi_option_filter.dart';

final testPlanNameFilter = createMultiOptionFilterFromExtractor(
  'Test Plan',
  (EnrichedTestExecution ee) => ee.testExecution.testPlan,
);

final enrichedTestExecutionFilters = [
  testPlanNameFilter,
];
