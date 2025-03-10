import '../models/enriched_test_execution.dart';
import '../models/environment_review.dart';
import 'multi_option_filter.dart';

final environmentReviewFilter = createMultiOptionFilterFromExtractor(
  'Review status',
  (EnrichedTestExecution ee) => switch (ee.environmentReview.reviewDecision) {
    [] => 'Undecided',
    [EnvironmentReviewDecision.rejected] => 'Rejected',
    [...] => 'Approved',
  },
);

final testPlanNameFilter = createMultiOptionFilterFromExtractor(
  'Test plan',
  (EnrichedTestExecution ee) {
    final testPlan = ee.testExecution.testPlan;
    return testPlan.isEmpty ? 'Unknown' : testPlan;
  },
);

final enrichedTestExecutionFilters = [
  environmentReviewFilter,
  testPlanNameFilter,
];
