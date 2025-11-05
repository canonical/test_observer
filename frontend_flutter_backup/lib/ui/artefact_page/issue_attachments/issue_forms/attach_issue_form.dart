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

import '../../../../models/attachment_rule_filters.dart';
import '../../../../models/test_results_filters.dart';
import '../../../../models/attachment_rule.dart';
import '../../../../providers/issue.dart';
import '../../../../providers/test_results.dart';
import '../../../issues.dart';
import '../../../notification.dart';
import '../../../spacing.dart';
import 'bulk_attach_section.dart';
import 'attachment_rule_section.dart';
import 'create_attachment_rule_section.dart';

class AttachIssueForm extends ConsumerStatefulWidget {
  final int testExecutionId;
  final int testResultId;
  final int artefactId;

  const AttachIssueForm({
    super.key,
    required this.testExecutionId,
    required this.testResultId,
    required this.artefactId,
  });

  @override
  ConsumerState<AttachIssueForm> createState() => _AttachIssueFormState();
}

class _AttachIssueFormState extends ConsumerState<AttachIssueForm> {
  late final GlobalKey<FormState> formKey;
  String _issueUrl = '';
  bool _createAttachmentRule = false;
  AttachmentRuleFilters _attachmentRuleFilters = AttachmentRuleFilters();
  bool _attachToOlderResults = false;
  bool _attachToNewerResults = false;

  @override
  void initState() {
    super.initState();
    formKey = GlobalKey<FormState>();
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;
    final testResult = ref
        .watch(
          testResultsProvider(widget.testExecutionId).select(
            (value) => value.whenData(
              (results) => results
                  .firstWhere((result) => result.id == widget.testResultId),
            ),
          ),
        )
        .value;
    final issueAttachments = testResult?.issueAttachments ?? [];

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Attach Issue', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: Spacing.level4),
            Flexible(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.6,
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    spacing: Spacing.level3,
                    children: [
                      IssueUrlFormField(
                        allowInternalIssue: true,
                        onChanged: (value) {
                          setState(() {
                            _issueUrl = value;
                          });
                        },
                      ),
                      CreateAttachmentRuleSection(
                        value: _createAttachmentRule,
                        onChanged: (checked) {
                          setState(() {
                            _createAttachmentRule = checked;
                          });
                        },
                      ),
                      if (_createAttachmentRule)
                        AttachmentRuleSection(
                          artefactId: widget.artefactId,
                          testResult: testResult,
                          testExecutionId: widget.testExecutionId,
                          selectedFilters: _attachmentRuleFilters,
                          onChanged: (filters) {
                            setState(() {
                              _attachmentRuleFilters = filters;
                            });
                          },
                        ),
                      if (_createAttachmentRule && testResult != null)
                        BulkAttachSection(
                          splitTime: testResult.createdAt,
                          attachmentRuleFilters: _attachmentRuleFilters,
                          selectedBulkAttachOlder: _attachToOlderResults,
                          selectedBulkAttachNewer: _attachToNewerResults,
                          onBulkAttachOlderChanged: (checked) {
                            setState(() {
                              _attachToOlderResults = checked;
                            });
                          },
                          onBulkAttachNewerChanged: (checked) {
                            setState(() {
                              _attachToNewerResults = checked;
                            });
                          },
                        ),
                    ],
                  ),
                ),
              ),
            ),
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
                    // Ensure the form is valid before proceeding.
                    if (formKey.currentState?.validate() != true) return;

                    // Get or create the issue ID.
                    final issueId = await getOrCreateIssueId(ref, _issueUrl);

                    // Create the attachment rule if requested.
                    AttachmentRule? attachmentRule;
                    if (_createAttachmentRule) {
                      attachmentRule = await ref
                          .read(issueProvider(issueId).notifier)
                          .createAttachmentRule(
                            issueId: issueId,
                            enabled: true,
                            filters: _attachmentRuleFilters,
                          );
                    }

                    // Check if the issue is already attached.
                    final issueAlreadyAttached = issueAttachments
                        .map((attachment) => attachment.issue.id)
                        .contains(issueId);

                    // Attach the issue to the test result.
                    await ref
                        .read(
                          testResultsProvider(widget.testExecutionId).notifier,
                        )
                        .attachIssueToTestResult(
                          widget.testResultId,
                          issueId,
                          attachmentRule: attachmentRule,
                        );

                    // Create the bulk attachment if requested.
                    if (_createAttachmentRule &&
                        (_attachToNewerResults || _attachToOlderResults)) {
                      TestResultsFilters testResultsFilters =
                          _attachmentRuleFilters.toTestResultsFilters();
                      if (!_attachToOlderResults) {
                        testResultsFilters = testResultsFilters.copyWith(
                          fromDate: testResult?.createdAt,
                        );
                      }
                      if (!_attachToNewerResults) {
                        testResultsFilters = testResultsFilters.copyWith(
                          untilDate: testResult?.createdAt,
                        );
                      }
                      await ref
                          .read(issueProvider(issueId).notifier)
                          .attachIssueToTestResults(
                            issueId: issueId,
                            filters: testResultsFilters,
                            attachmentRuleId: attachmentRule?.id,
                          );
                    }

                    // Note that the issue was already attached.
                    if (!context.mounted) return;
                    if (issueAlreadyAttached) {
                      showNotification(
                        context,
                        'Note: Issue already attached.',
                      );
                    }
                    Navigator.of(context).pop();
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
  required int artefactId,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: AttachIssueForm(
            testExecutionId: testExecutionId,
            testResultId: testResultId,
            artefactId: artefactId,
          ),
        ),
      ),
    );
