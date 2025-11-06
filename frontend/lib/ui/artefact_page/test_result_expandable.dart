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
import 'package:yaru/widgets.dart';

import '../../models/test_result.dart';
import '../../providers/artefact.dart';
import '../../providers/test_result_issues.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'test_issues/test_issues_expandable.dart';
import 'issue_attachments/issue_attachments_expandable.dart';

class TestResultExpandable extends ConsumerWidget {
  const TestResultExpandable({
    super.key,
    required this.testExecutionId,
    required this.testResult,
    required this.artefactId,
    this.testResultIdToExpand,
  });

  final int testExecutionId;
  final TestResult testResult;
  final int artefactId;
  final String? testResultIdToExpand;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    String title = testResult.name;
    if (issues.length == 1) {
      title += ' (${issues.length} reported issue)';
    } else if (issues.length > 1) {
      title += ' (${issues.length} reported issues)';
    }

    final initiallyExpanded = testResultIdToExpand != null &&
        testResult.id == int.tryParse(testResultIdToExpand!);

    return Expandable(
      initiallyExpanded: initiallyExpanded,
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          _PreviousTestResultsWidget(
            currentResult: testResult,
            previousResults: testResult.previousResults,
          ),
        ],
      ),
      children: [
        TestIssuesExpandable(testResult: testResult),
        IssueAttachmentsExpandable(
          testExecutionId: testExecutionId,
          testResultId: testResult.id,
          artefactId: artefactId,
        ),
        _TestResultOutputExpandable(testResult: testResult),
      ],
    );
  }
}

class _TestResultOutputExpandable extends StatelessWidget {
  const _TestResultOutputExpandable({required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      title: const Text('Details'),
      initiallyExpanded: true,
      children: [
        if (testResult.category != '')
          YaruTile(
            title: const Text('Category'),
            subtitle: Text(testResult.category),
          ),
        if (testResult.comment != '')
          YaruTile(
            title: const Text('Comment'),
            subtitle: Text(testResult.comment),
          ),
        if (testResult.ioLog != '')
          YaruTile(
            title: const Text('IO Log'),
            subtitle: Text(testResult.ioLog),
          ),
      ],
    );
  }
}

class _PreviousTestResultsWidget extends ConsumerWidget {
  const _PreviousTestResultsWidget({
    required this.currentResult,
    required this.previousResults,
  });

  final TestResult currentResult;
  final List<PreviousTestResult> previousResults;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));
    final currentVersion = ref
            .watch(
              artefactProvider(artefactId)
                  .select((data) => data.whenData((a) => a.version)),
            )
            .value ??
        'unknown';

    if (previousResults.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(left: Spacing.level2),
      child: PopupMenuButton(
        tooltip: 'Previous test results',
        itemBuilder: (context) {
          return previousResults
              .map(
                (result) => PopupMenuItem(
                  enabled: result.version != currentVersion,
                  child: Text(
                    '${result.version} - ${result.status.name.toUpperCase()}',
                  ),
                ),
              )
              .toList();
        },
        child: const Text('prev'),
      ),
    );
  }
}
