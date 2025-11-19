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
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
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
  });

  final int testExecutionId;
  final TestResult testResult;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    String title = testResult.name;
    if (issues.length == 1) {
      title += ' (${issues.length} reported issue)';
    } else if (issues.length > 1) {
      title += ' (${issues.length} reported issues)';
    }

    return Expandable(
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
        '';

    final statusGroups = {
      currentVersion: [
        PreviousTestResult(
          artefactId: artefactId,
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
    return InkWell(
      onTap: (groupIndex > 0)
          ? () => navigateToArtefactPage(
                context,
                results.first.artefactId,
              )
          : null,
      child: Tooltip(
        message: 'Version: $version',
        child: Wrap(
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
        ),
      ),
    );
  }
}
