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

import '../../../models/test_results_filters.dart';
import '../../../providers/reruns.dart';
import '../../../providers/test_results_search.dart';
import '../../spacing.dart';

class _BulkModifyRerunsForm extends ConsumerStatefulWidget {
  const _BulkModifyRerunsForm(this.filters, this.shouldDelete);

  final TestResultsFilters filters;
  final bool shouldDelete;

  @override
  ConsumerState<_BulkModifyRerunsForm> createState() =>
      _BulkModifyRerunsFormState();
}

class _BulkModifyRerunsFormState extends ConsumerState<_BulkModifyRerunsForm> {
  late final GlobalKey<FormState> formKey;
  bool onlyLatestExecutions = true;
  bool excludeArchivedArtefacts = true;

  @override
  void initState() {
    super.initState();
    formKey = GlobalKey<FormState>();
  }

  @override
  void dispose() {
    super.dispose();
  }

  Widget _buildCheckbox({
    required String title,
    required bool value,
    required ValueChanged<bool?> onChanged,
  }) {
    return CheckboxListTile(
      title: Text(title),
      value: value,
      onChanged: onChanged,
      controlAffinity: ListTileControlAffinity.leading,
      contentPadding: EdgeInsets.zero,
    );
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    if (!widget.filters.hasFilters) {
      return const Text(
        'Cannot perform bulk rerun modification without any filters specified.',
      );
    }

    final modifyTestResultFilters = widget.filters.copyWith(
      rerunIsRequested: widget.shouldDelete,
      executionIsLatest:
          onlyLatestExecutions ? true : widget.filters.executionIsLatest,
      artefactIsArchived:
          excludeArchivedArtefacts ? false : widget.filters.artefactIsArchived,
    );

    final testResultsAsync = ref.watch(
      testResultsSearchProvider(modifyTestResultFilters.copyWith(limit: 0)),
    );
    if (testResultsAsync.isLoading) {
      return const UnconstrainedBox(child: CircularProgressIndicator());
    }
    if (testResultsAsync.hasError) {
      return const Text('Failed to load test results.');
    }
    final testResults = testResultsAsync.value;
    final testResultsCount = testResults?.count ?? 0;
    if (testResultsCount == 0) {
      if (widget.shouldDelete) {
        return const Text(
          'No test results have rerun requests.',
        );
      } else {
        return const Text(
          'No test results do not already have rerun requests.',
        );
      }
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
              widget.shouldDelete
                  ? 'Delete Rerun Requests'
                  : 'Create Rerun Requests',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            Text(
              '$testResultsCount matched test results will be affected.',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            _buildCheckbox(
              title: 'Only latest test executions',
              value: onlyLatestExecutions,
              onChanged: (value) {
                setState(() {
                  onlyLatestExecutions = value ?? true;
                });
              },
            ),
            _buildCheckbox(
              title: 'Exclude archived artefacts',
              value: excludeArchivedArtefacts,
              onChanged: (value) {
                setState(() {
                  excludeArchivedArtefacts = value ?? true;
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
                  key: const Key('bulkModifyRerunsFormSubmitButton'),
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
                            'You are about to ${widget.shouldDelete ? 'delete' : 'create'} rerun requests for over 50 test results. Do you want to proceed?',
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

                    // Submit the bulk operation.
                    if (widget.shouldDelete) {
                      await ref.read(rerunsProvider.notifier).deleteReruns(
                            filters: modifyTestResultFilters,
                          );
                    } else {
                      await ref.read(rerunsProvider.notifier).createReruns(
                            filters: modifyTestResultFilters,
                          );
                    }

                    // Close the form.
                    if (!context.mounted) return;
                    Navigator.of(context).pop();
                  },
                  child: widget.shouldDelete ? Text('delete') : Text('create'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showModifyRerunsDialog({
  required BuildContext context,
  required TestResultsFilters filters,
  bool shouldDelete = false,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _BulkModifyRerunsForm(filters, shouldDelete),
        ),
      ),
    );
