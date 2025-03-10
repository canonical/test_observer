import '../models/enriched_test_execution.dart';
import 'multi_option_filter.dart';

final testPlanNameFilter = createMultiOptionFilterFromExtractor(
  'Test plan',
  (EnrichedTestExecution ee) {
    final testPlan = ee.testExecution.testPlan;
    return testPlan.isEmpty ? 'Unknown' : testPlan;
  },
);

final enrichedTestExecutionFilters = [
  testPlanNameFilter,
];
