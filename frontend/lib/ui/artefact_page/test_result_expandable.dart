// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';
import 'package:intersperse/intersperse.dart';
import 'package:dartx/dartx.dart';

import '../../models/test_result.dart';
import '../../providers/artefact.dart';
import '../../providers/test_result_issues.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../navigable_link.dart';
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
  final int? testResultIdToExpand;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    String title = testResult.name;
    if (issues.length == 1) {
      title += ' (${issues.length} reported issue)';
    } else if (issues.length > 1) {
      title += ' (${issues.length} reported issues)';
    }

    final initiallyExpanded =
        testResultIdToExpand != null && testResult.id == testResultIdToExpand;

    return Expandable(
      initiallyExpanded: initiallyExpanded,
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          _PreviousTestResultsWidget(
            testExecutionId: testExecutionId,
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
            subtitle: SelectableText(
              testResult.ioLog,
              style: const TextStyle(
                fontFamily: 'UbuntuMono',
                fontSize: 12,
              ),
            ),
          ),
      ],
    );
  }
}

class _PreviousTestResultsWidget extends ConsumerWidget {
  const _PreviousTestResultsWidget({
    required this.testExecutionId,
    required this.currentResult,
    required this.previousResults,
  });

  final int testExecutionId;
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
        '';

    final statusGroups = {
      currentVersion: [
        PreviousTestResult(
          artefactId: artefactId,
          testExecutionId: testExecutionId,
          testResultId: currentResult.id,
          status: currentResult.status,
          version: currentVersion,
        ),
      ],
    };
    for (final result in previousResults) {
      final statuses = statusGroups[result.version];
      if (statuses != null) {
        statuses.add(result);
      } else {
        statusGroups[result.version] = [result];
      }
    }

    return Row(
      children: statusGroups.entries
          .mapIndexed<Widget>(
            (groupIndex, entry) => _TestResultsGroup(
              groupIndex: groupIndex,
              version: entry.key,
              results: entry.value,
            ),
          )
          .reversed
          .intersperse(const SizedBox(width: Spacing.level2))
          .toList(),
    );
  }
}

class _TestResultsGroup extends StatelessWidget {
  const _TestResultsGroup({
    required this.groupIndex,
    required this.version,
    required this.results,
  });

  final int groupIndex;
  final String version;
  final List<PreviousTestResult> results;

  @override
  Widget build(BuildContext context) {
    final hasNavigation = groupIndex > 0;
    final result = hasNavigation ? results.first : null;
    final path = hasNavigation
        ? getArtefactPagePath(
            context,
            result!.artefactId,
            testExecutionId: result.testExecutionId,
            testResultId: result.testResultId,
          )
        : null;

    final content = Wrap(
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: -5,
      children: results
          .mapIndexed(
            (index, result) => Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                shape: BoxShape.circle,
              ),
              child: result.status.getIcon(
                scale: (groupIndex == index && index == 0) ? 1.5 : 1,
              ),
            ),
          )
          .reversed
          .toList(),
    );

    if (hasNavigation) {
      return NavigableLink(
        path: path!,
        tooltip: 'Version: $version',
        semanticsLabel: 'View test results for version $version',
        child: content,
      );
    }

    return Tooltip(
      message: 'Version: $version',
      child: content,
    );
  }
}
