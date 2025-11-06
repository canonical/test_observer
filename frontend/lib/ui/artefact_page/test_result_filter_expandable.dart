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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import '../../../models/test_result.dart';
import '../../../providers/test_results.dart';
import '../../../ui/test_results_page/test_results_helpers.dart';
import '../expandable.dart';
import 'test_result_expandable.dart';

class TestResultsFilterExpandable extends ConsumerWidget {
  const TestResultsFilterExpandable({
    super.key,
    required this.statusToFilterBy,
    required this.testExecutionId,
    required this.artefactId,
    this.testResultIdToExpand,
  });

  final TestResultStatus statusToFilterBy;
  final int testExecutionId;
  final int artefactId;
  final String? testResultIdToExpand;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testResultsAsync = ref.watch(testResultsProvider(testExecutionId));

    return testResultsAsync.when(
      loading: () => const CircularProgressIndicator(),
      error: (error, stackTrace) => Text('Error: $error'),
      data: (testResults) {
        final filteredResults = testResults
            .where((result) => result.status == statusToFilterBy)
            .toList();

        final shouldExpandStatus = testResultIdToExpand != null &&
            filteredResults.any(
              (result) => result.id == int.tryParse(testResultIdToExpand!),
            );

        return Expandable(
          initiallyExpanded: shouldExpandStatus,
          title: Row(
            children: [
              TestResultHelpers.getStatusIcon(statusToFilterBy),
              const SizedBox(width: 8),
              Text(statusToFilterBy.name),
              Text(' ${filteredResults.length}'),
            ],
          ),
          children: filteredResults
              .map(
                (result) => TestResultExpandable(
                  testExecutionId: testExecutionId,
                  testResult: result,
                  artefactId: artefactId,
                  testResultIdToExpand: testResultIdToExpand,
                ),
              )
              .toList(),
        );
      },
    );
  }
}
