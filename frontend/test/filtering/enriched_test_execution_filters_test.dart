// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:test/test.dart';
import 'package:testcase_dashboard/filtering/enriched_test_execution_filters.dart';
import 'package:testcase_dashboard/models/enriched_test_execution.dart';

import '../dummy_data.dart';

void main() {
  final executionWithNoReviewer = EnrichedTestExecution(
    testExecution: dummyTestExecution,
    environmentReview: dummyEnvironmentReview,
  );

  final executionWithSingleReviewer = EnrichedTestExecution(
    testExecution: dummyTestExecution2,
    environmentReview: dummyEnvironmentReviewWithReviewer,
  );

  final executionWithMultipleReviewers = EnrichedTestExecution(
    testExecution: dummyTestExecution2.copyWith(id: 3),
    environmentReview: dummyEnvironmentReviewWithReviewer.copyWith(
      id: 3,
      reviewers: [dummyUser, dummyUser2],
    ),
  );

  test('extractOptions includes reviewer labels and unassigned option', () {
    final options = environmentReviewerFilter.extractOptions([
      executionWithNoReviewer,
      executionWithSingleReviewer,
    ]);

    expect(options, contains(noEnvironmentReviewerAssignedOption));
    expect(options, contains('Dummy User (dummy.user@canonical.com)'));
  });

  test('filter returns executions with selected reviewer', () {
    final filtered = environmentReviewerFilter.filter([
      executionWithNoReviewer,
      executionWithSingleReviewer,
    ], {
      'Dummy User (dummy.user@canonical.com)',
    });

    expect(filtered, [executionWithSingleReviewer]);
  });

  test('filter returns unassigned executions for unassigned option', () {
    final filtered = environmentReviewerFilter.filter([
      executionWithNoReviewer,
      executionWithSingleReviewer,
    ], {
      noEnvironmentReviewerAssignedOption,
    });

    expect(filtered, [executionWithNoReviewer]);
  });

  test('filter matches any reviewer assigned to an environment review', () {
    final filtered = environmentReviewerFilter.filter([
      executionWithSingleReviewer,
      executionWithMultipleReviewers,
    ], {
      'John Doe (john.doe@canonical.com)',
    });

    expect(filtered, [executionWithMultipleReviewers]);
  });
}
