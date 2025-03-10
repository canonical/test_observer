// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:dartx/dartx.dart';

import '../models/enriched_test_execution.dart';
import '../models/environment_review.dart';
import 'filter.dart';

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

final testPlanLastStatusFilter = Filter<EnrichedTestExecution>(
  name: 'Plans whose last run',
  extractOptions: (items) {
    final groups = items
        .groupBy((ee) => (ee.environmentReview.id, ee.testExecution.testPlan));
    final options = <String>{};
    for (var enrichedExecutions in groups.values) {
      final lastExecution =
          enrichedExecutions.maxBy((ee) => ee.testExecution.id);
      if (lastExecution != null) {
        options.add(lastExecution.testExecution.status.name);
      }
    }
    return options;
  },
  filter: (items, options) {
    final groups = items
        .groupBy((ee) => (ee.environmentReview.id, ee.testExecution.testPlan));
    final filteredGroups = groups.entries.filter((entry) {
      final lastStatus =
          entry.value.maxBy((ee) => ee.testExecution.id)?.testExecution.status;
      return lastStatus != null && options.contains(lastStatus.name);
    });
    return [
      for (var group in filteredGroups)
        for (var ee in group.value) ee,
    ];
  },
);

final enrichedTestExecutionFilters = [
  environmentReviewFilter,
  testPlanLastStatusFilter,
  testPlanNameFilter,
];
