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
import 'package:go_router/go_router.dart';

import '../../../../models/issue.dart';
import '../../../../providers/test_results.dart';
import '../../../../routing.dart';
import '../../../spacing.dart';
import '../issue_widget.dart';

class _DetachIssueDialog extends ConsumerWidget {
  const _DetachIssueDialog({
    required this.issue,
    required this.testExecutionId,
    required this.testResultId,
  });

  final Issue issue;
  final int testExecutionId;
  final int testResultId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AlertDialog(
      title: const Text('Are you sure you want to detach this issue?'),
      content: SizedBox(
        width: Spacing.formWidth,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {
            navigateToIssuePage(context, issue.id);
          },
          child: Card(
            child: Padding(
              padding: const EdgeInsets.symmetric(
                vertical: Spacing.level3,
                horizontal: Spacing.level4,
              ),
              child: IssueWidget(issue: issue),
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            context.pop(false);
          },
          child: const Text('No'),
        ),
        TextButton(
          key: const Key('detachIssueConfirmButton'),
          onPressed: () async {
            await ref
                .read(testResultsProvider(testExecutionId).notifier)
                .detachIssueFromTestResult(testResultId, issue.id);
            if (!context.mounted) return;
            Navigator.of(context).pop();
          },
          child: const Text('Yes'),
        ),
      ],
    );
  }
}

void showDetachIssueDialog({
  required BuildContext context,
  required Issue issue,
  required int testResultId,
  required int testExecutionId,
}) =>
    showDialog(
      context: context,
      builder: (_) => _DetachIssueDialog(
        issue: issue,
        testExecutionId: testExecutionId,
        testResultId: testResultId,
      ),
    );
