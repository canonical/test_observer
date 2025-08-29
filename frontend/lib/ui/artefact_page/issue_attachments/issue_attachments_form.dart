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

import '../../../models/issue.dart';
import '../../../providers/issues.dart';
import '../../../providers/test_results.dart';
import '../../notification.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_text_input.dart';
import 'issue_widget.dart';

class _AttachIssueForm extends ConsumerWidget {
  final int testExecutionId;
  final int testResultId;

  const _AttachIssueForm({
    required this.testExecutionId,
    required this.testResultId,
  });

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final formKey = GlobalKey<FormState>();
    final urlController = TextEditingController();
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    final issueAttachments = ref
            .watch(
              testResultsProvider(testExecutionId).select(
                (value) => value.whenData(
                  (results) => results
                      .firstWhere((result) => result.id == testResultId)
                      .issueAttachments,
                ),
              ),
            )
            .value ??
        [];

    return Form(
      key: formKey,
      child: SizedBox(
        width: 700,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Attach Issue', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: Spacing.level4),
            VanillaTextInput(
              key: const Key('attachIssueFormUrlInput'),
              label:
                  'Test Observer issue URL or external URL (GitHub, Jira, Launchpad)',
              controller: urlController,
              validator: (value) {
                if (value == null || value.isEmpty) {
                  return 'Please enter a URL';
                }
                final uri = Uri.tryParse(value);
                if (uri == null || !uri.hasScheme || !uri.hasAuthority) {
                  return 'Please enter a valid URL';
                }
                if (uri.origin == Uri.base.origin) {
                  final regExp = RegExp(r'^/issues/\d+$');
                  if (regExp.hasMatch(uri.fragment) == false) {
                    return 'Invalid Test Observer issue URL, expected: ${Uri.base.origin}/#/issues/<id>';
                  }
                }
                return null;
              },
            ),
            const SizedBox(height: Spacing.level3),
            Row(
              children: [
                TextButton(
                  onPressed: () => context.pop(),
                  child: Text(
                    'cancel',
                    style: buttonFontStyle?.apply(color: Colors.grey),
                  ),
                ),
                const Spacer(),
                TextButton(
                  key: const Key('attachIssueFormSubmitButton'),
                  onPressed: () async {
                    if (formKey.currentState?.validate() != true) return;
                    final url = urlController.text.trim();
                    final uri = Uri.parse(url);
                    int issueId;
                    if (uri.origin == Uri.base.origin) {
                      final regExp = RegExp(r'^/issues/(\d+)$');
                      final match = regExp.firstMatch(uri.fragment);
                      issueId = int.parse(match!.group(1)!);
                    } else {
                      final issue = await ref
                          .read(issuesProvider.notifier)
                          .createIssue(url: url);
                      issueId = issue.id;
                    }
                    final issueAppearsAttached = issueAttachments
                        .map((attachment) => attachment.issue.id)
                        .contains(issueId);
                    // Don't use context after await, store pop and notification in local callbacks
                    void popDialog() => Navigator.of(context).pop();
                    void showAlreadyAttached() => showNotification(
                          context,
                          'Note: Issue already attached.',
                        );
                    await ref
                        .read(testResultsProvider(testExecutionId).notifier)
                        .attachIssueToTestResult(testResultId, issueId);
                    popDialog();
                    if (issueAppearsAttached) {
                      showAlreadyAttached();
                    }
                  },
                  child: Text(
                    'attach',
                    style: buttonFontStyle?.apply(color: Colors.black),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showAttachIssueDialog({
  required BuildContext context,
  required int testExecutionId,
  required int testResultId,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _AttachIssueForm(
            testExecutionId: testExecutionId,
            testResultId: testResultId,
          ),
        ),
      ),
    );

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
        width: 700,
        child: InkWell(
          borderRadius: BorderRadius.circular(12),
          onTap: () {
            Navigator.of(context).pushNamed('/issues/${issue.id}');
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
            void popDialog() => Navigator.of(context).pop();
            await ref
                .read(testResultsProvider(testExecutionId).notifier)
                .detachIssueFromTestResult(testResultId, issue.id);
            popDialog();
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
