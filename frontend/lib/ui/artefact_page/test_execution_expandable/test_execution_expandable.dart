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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_execution.dart';
import '../../../models/test_result.dart';
import '../../../routing.dart';
import '../../expandable.dart';
import '../../inline_url_text.dart';
import '../../spacing.dart';
import '../test_result_filter_expandable.dart';
import '../test_event_log_expandable.dart';
import '../execution_metadata_expandable.dart';
import '../test_result_dialog.dart';
import '../../../providers/current_user.dart';
import '../manual_testing_dialog.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({
    super.key,
    required this.artefactId,
    required this.testExecution,
    required this.runNumber,
    this.initiallyExpanded = false,
  });

  final int artefactId;
  final TestExecution testExecution;
  final int runNumber;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final testResultIdString = pageUri.queryParameters['testResultId'];
    final testResultIdToExpand =
        testResultIdString != null ? int.tryParse(testResultIdString) : null;

    return Expandable(
      initiallyExpanded: initiallyExpanded,
      title: _TestExecutionTileTitle(
        testExecution: testExecution,
        runNumber: runNumber,
        artefactId: artefactId,
      ),
      children: <Widget>[
        if (testExecution.testPlan != kManualTestPlanName)
          TestEventLogExpandable(
            testExecutionId: testExecution.id,
            initiallyExpanded: !testExecution.status.isCompleted,
          ),
        if (testExecution.testPlan != kManualTestPlanName)
          ExecutionMetadataExpandable(
            executionMetadata: testExecution.executionMetadata,
            initiallyExpanded: false,
          ),
        if (testExecution.status.isCompleted ||
            testExecution.testPlan == kManualTestPlanName)
          Expandable(
            title: const Text('Test Results'),
            initiallyExpanded: true,
            children: TestResultStatus.values
                .map(
                  (status) => TestResultsFilterExpandable(
                    statusToFilterBy: status,
                    testExecutionId: testExecution.id,
                    artefactId: artefactId,
                    testResultIdToExpand: testResultIdToExpand,
                  ),
                )
                .toList(),
          ),
      ],
    );
  }
}

class _TestExecutionTileTitle extends ConsumerWidget {
  const _TestExecutionTileTitle({
    required this.testExecution,
    required this.runNumber,
    required this.artefactId,
  });

  final TestExecution testExecution;
  final int runNumber;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;
    final relevantLinks = testExecution.relevantLinks;
    final user = ref.watch(currentUserProvider).value;

    return Row(
      children: [
        testExecution.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          'Run $runNumber',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const Spacer(),
        if (ciLink != null)
          InlineUrlText(
            url: ciLink,
            urlText: 'CI',
          ),
        const SizedBox(width: Spacing.level3),
        if (c3Link != null)
          InlineUrlText(
            url: c3Link,
            urlText: 'C3',
          ),
        for (final link in relevantLinks)
          Padding(
            padding: const EdgeInsets.only(left: Spacing.level3),
            child: InlineUrlText(
              url: link.url,
              urlText: link.label,
            ),
          ),
        if (user != null && testExecution.testPlan == kManualTestPlanName) ...[
          const SizedBox(width: Spacing.level3),
          TextButton.icon(
            onPressed: () => showDialog(
              context: context,
              builder: (_) => AddTestResultDialog(
                testExecutionId: testExecution.id,
                artefactId: artefactId,
              ),
            ),
            label: const Text('Add Test Result'),
            style: TextButton.styleFrom(
              padding: const EdgeInsets.symmetric(
                horizontal: 12,
                vertical: 8,
              ),
            ),
          ),
        ],
      ],
    );
  }
}
