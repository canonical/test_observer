// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import '../../../models/test_results_filters.dart';
import '../../../providers/issue.dart';
import '../../../providers/test_results_search.dart';
import '../../issues.dart';
import '../../spacing.dart';

class _BulkIssueAttachmentForm extends ConsumerStatefulWidget {
  const _BulkIssueAttachmentForm(this.filters, this.shouldDetach);

  final TestResultsFilters filters;
  final bool shouldDetach;

  @override
  ConsumerState<_BulkIssueAttachmentForm> createState() =>
      _BulkIssueAttachmentFormState();
}

class _BulkIssueAttachmentFormState
    extends ConsumerState<_BulkIssueAttachmentForm> {
  late final GlobalKey<FormState> formKey;
  String _issueUrl = '';

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

    final testResultsAsync =
        ref.watch(testResultsSearchProvider(widget.filters));
    if (testResultsAsync.isLoading) {
      return const UnconstrainedBox(child: CircularProgressIndicator());
    }
    if (testResultsAsync.hasError) {
      return const Text('Failed to load test results.');
    }
    final testResults = testResultsAsync.value;
    final testResultsCount = testResults?.count ?? 0;
    if (testResultsCount == 0) {
      return const Text('No test results match the current filters.');
    }

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: Spacing.level4,
          children: [
            Text(
              widget.shouldDetach
                  ? 'Detach the issue from the $testResultsCount selected test results'
                  : 'Attach the issue to the $testResultsCount selected test results',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            IssueUrlFormField(
              allowInternalIssue: true,
              onChanged: (value) {
                setState(() {
                  _issueUrl = value;
                });
              },
            ),
            Row(
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(
                    'cancel',
                    style: buttonFontStyle?.apply(color: Colors.grey),
                  ),
                ),
                const Spacer(),
                TextButton(
                  key: const Key('bulkIssueAttachmentFormSubmitButton'),
                  onPressed: () async {
                    // Ensure the form is valid before proceeding.
                    if (formKey.currentState?.validate() != true) return;

                    // Double check if there are many many test results
                    if (testResultsCount > 50) {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (context) => AlertDialog(
                          title: const Text('Confirm Bulk Operation'),
                          content: Text(
                            'You are about to ${widget.shouldDetach ? 'detach' : 'attach'} an issue to over 50 test results. Do you want to proceed?',
                          ),
                          actions: [
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(false),
                              child: const Text('cancel'),
                            ),
                            TextButton(
                              onPressed: () => Navigator.of(context).pop(true),
                              child: const Text('proceed'),
                            ),
                          ],
                        ),
                      );
                      if (confirm != true) {
                        return;
                      }
                    }

                    // Create or get the issue.
                    final issueId = await getOrCreateIssueId(ref, _issueUrl);

                    // Submit the bulk operation.
                    if (widget.shouldDetach) {
                      await ref
                          .read(issueProvider(issueId).notifier)
                          .detachIssueFromTestResults(
                            issueId: issueId,
                            filters: widget.filters,
                          );
                    } else {
                      await ref
                          .read(issueProvider(issueId).notifier)
                          .attachIssueToTestResults(
                            issueId: issueId,
                            filters: widget.filters,
                          );
                    }

                    // Close the form.
                    if (!context.mounted) return;
                    Navigator.of(context).pop();
                  },
                  child: widget.shouldDetach ? Text('detach') : Text('attach'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showBulkIssueAttachmentDialog({
  required BuildContext context,
  required TestResultsFilters filters,
  bool shouldDetach = false,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _BulkIssueAttachmentForm(filters, shouldDetach),
        ),
      ),
    );
