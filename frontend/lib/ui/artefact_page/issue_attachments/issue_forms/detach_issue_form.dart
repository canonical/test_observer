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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../../models/attachment_rule_filters.dart';
import '../../../../models/issue.dart';
import '../../../../models/test_results_filters.dart';
import '../../../../providers/test_results.dart';
import '../../../../providers/issue.dart' as ip;
import '../../../../routing.dart';
import '../../../attachment_rule.dart';
import '../../../spacing.dart';
import '../issue_widget.dart';
import 'bulk_attach_section.dart';

class DetachIssueForm extends ConsumerStatefulWidget {
  final Issue issue;
  final int testExecutionId;
  final int testResultId;

  const DetachIssueForm({
    super.key,
    required this.issue,
    required this.testExecutionId,
    required this.testResultId,
  });

  @override
  ConsumerState<DetachIssueForm> createState() => _DetachIssueFormState();
}

class _DetachIssueFormState extends ConsumerState<DetachIssueForm> {
  late final GlobalKey<FormState> formKey;
  bool _disableAttachmentRule = false;
  bool _deleteNewerAttachments = false;

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
    final issueAttachment = testResult?.issueAttachments.firstOrNullWhere(
      (attachment) => attachment.issue.id == widget.issue.id,
    );
    final attachmentRule = issueAttachment?.attachmentRule;
    final attachmentRuleFilters = attachmentRule != null
        ? AttachmentRuleFilters.fromAttachmentRule(attachmentRule)
        : null;
    final deleteNewerAttachmentsTestResultFilters =
        attachmentRuleFilters != null
            ? attachmentRuleFilters.toTestResultsFilters().copyWith(
                  issues: IssuesFilter.list([widget.issue.id]),
                  fromDate: testResult?.createdAt,
                )
            : null;

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Detach Issue', style: Theme.of(context).textTheme.titleLarge),
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
                      InkWell(
                        borderRadius: BorderRadius.circular(12),
                        onTap: () {
                          navigateToIssuePage(context, widget.issue.id);
                        },
                        child: Card(
                          child: Padding(
                            padding: const EdgeInsets.symmetric(
                              vertical: Spacing.level3,
                              horizontal: Spacing.level4,
                            ),
                            child: IssueWidget(issue: widget.issue),
                          ),
                        ),
                      ),
                      if (attachmentRule != null) ...[
                        CheckboxListTile(
                          key: const Key('disableAttachmentRuleCheckbox'),
                          title: Text('Disable attachment rule'),
                          value: _disableAttachmentRule,
                          onChanged: attachmentRule.enabled
                              ? (selected) {
                                  setState(() {
                                    _disableAttachmentRule = selected ?? false;
                                  });
                                }
                              : null,
                        ),
                        Card(
                          margin: const EdgeInsets.only(
                            left: 12.0,
                            top: 8.0,
                            bottom: 8.0,
                            right: 0,
                          ),
                          elevation: 1.5,
                          child: Padding(
                            padding: const EdgeInsets.all(12.0),
                            child: AttachmentRuleFiltersWidget(
                              filters: attachmentRuleFilters!,
                              editable: false,
                            ),
                          ),
                        ),
                        BulkAttachIssueOption(
                          title: 'Detach for newer test results',
                          value: _deleteNewerAttachments,
                          filters: deleteNewerAttachmentsTestResultFilters!,
                          loadNumberResults:
                              deleteNewerAttachmentsTestResultFilters
                                  .hasFilters,
                          onChanged: (selected) {
                            setState(() {
                              _deleteNewerAttachments = selected;
                            });
                          },
                        ),
                      ],
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
                  key: const Key('detachIssueFormSubmitButton'),
                  onPressed: () async {
                    // Ensure the form is valid before proceeding.
                    if (formKey.currentState?.validate() != true) return;

                    // Disable the attachment rule if requested
                    if (attachmentRule != null && _disableAttachmentRule) {
                      await ref
                          .read(ip.issueProvider(widget.issue.id).notifier)
                          .disableAttachmentRule(
                            issueId: widget.issue.id,
                            attachmentRuleId: attachmentRule.id,
                          );
                    }

                    // Create the bulk detachment if requested.
                    if (deleteNewerAttachmentsTestResultFilters != null &&
                        _deleteNewerAttachments) {
                      await ref
                          .read(ip.issueProvider(widget.issue.id).notifier)
                          .detachIssueFromTestResults(
                            issueId: widget.issue.id,
                            filters: deleteNewerAttachmentsTestResultFilters,
                          );
                    }

                    // Detach the issue from the test result.
                    await ref
                        .read(
                          testResultsProvider(widget.testExecutionId).notifier,
                        )
                        .detachIssueFromTestResult(
                          widget.testResultId,
                          widget.issue.id,
                        );

                    // Finish up.
                    if (!context.mounted) return;
                    Navigator.of(context).pop();
                  },
                  child: Text(
                    'detach',
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

void showDetachIssueDialog({
  required BuildContext context,
  required Issue issue,
  required int testResultId,
  required int testExecutionId,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: DetachIssueForm(
            issue: issue,
            testExecutionId: testExecutionId,
            testResultId: testResultId,
          ),
        ),
      ),
    );
