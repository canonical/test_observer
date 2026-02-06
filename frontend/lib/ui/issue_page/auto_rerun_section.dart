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
import 'package:yaru/yaru.dart';

import '../../models/issue.dart';
import '../../models/test_results_filters.dart';
import '../../providers/issue.dart';
import '../../providers/test_results_search.dart';
import '../inline_url_text.dart';

class AutoRerunSection extends ConsumerWidget {
  const AutoRerunSection({
    super.key,
    required this.issue,
  });

  final IssueWithContext issue;

  Future<Map<String, bool>?> _showAutoRerunOptionsDialog(
    BuildContext context,
  ) async {
    bool rerunExisting = true; // Default to true
    bool onlyLatest = true; // Default to true for initial rerun
    bool excludeArchived = true; // Default to true for initial rerun

    return showDialog<Map<String, bool>>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => Consumer(
          builder: (context, ref, _) {
            // Build filters based on current checkbox state
            final filters = TestResultsFilters(
              issues: IntListFilter.list([issue.id]),
              executionIsLatest: rerunExisting && onlyLatest ? true : null,
              artefactIsArchived:
                  rerunExisting && excludeArchived ? false : null,
            );

            // Always watch the provider
            final testResultsAsync = ref.watch(
              testResultsSearchProvider(filters.copyWith(limit: 0)),
            );

            final isLoading = testResultsAsync.isLoading;
            final hasError = testResultsAsync.hasError;
            final testResultsCount = testResultsAsync.hasValue
                ? (testResultsAsync.value?.count ?? 0)
                : 0;

            return AlertDialog(
              title: const Text('Enable Automatic Reruns'),
              content: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'When enabled, test results attached to this issue will automatically have rerun requests created.',
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'Select rerun options:',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  CheckboxListTile(
                    title: const Text('Rerun existing test results'),
                    subtitle: const Text(
                        'Trigger reruns for currently attached test results',
                    ),
                    value: rerunExisting,
                    onChanged: (value) {
                      setState(() {
                        rerunExisting = value ?? true;
                      });
                    },
                    controlAffinity: ListTileControlAffinity.leading,
                    contentPadding: EdgeInsets.zero,
                  ),
                  if (rerunExisting) ...[
                    Padding(
                      padding: const EdgeInsets.only(left: 32.0),
                      child: Column(
                        children: [
                          CheckboxListTile(
                            title: const Text('Only latest test executions'),
                            value: onlyLatest,
                            onChanged: (value) {
                              setState(() {
                                onlyLatest = value ?? true;
                              });
                            },
                            controlAffinity: ListTileControlAffinity.leading,
                            contentPadding: EdgeInsets.zero,
                          ),
                          CheckboxListTile(
                            title: const Text('Exclude archived artefacts'),
                            value: excludeArchived,
                            onChanged: (value) {
                              setState(() {
                                excludeArchived = value ?? true;
                              });
                            },
                            controlAffinity: ListTileControlAffinity.leading,
                            contentPadding: EdgeInsets.zero,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                    if (isLoading)
                      const SizedBox(
                        width: 24,
                        height: 24,
                        child: YaruCircularProgressIndicator(),
                      )
                    else if (hasError)
                      const Text(
                        'Failed to load test results.',
                        style: TextStyle(color: Colors.red),
                      )
                    else
                      InlineUrlText(
                        url: '/#${filters.toTestResultsUri()}',
                        urlText: 'Matches $testResultsCount test results',
                        fontStyle: Theme.of(context).textTheme.bodyLarge?.apply(
                              color: Theme.of(context).colorScheme.primary,
                              fontStyle: FontStyle.italic,
                              decoration: TextDecoration.none,
                            ),
                      ),
                  ],
                ],
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () => Navigator.of(context).pop({
                    'rerunExisting': rerunExisting,
                    'onlyLatest': rerunExisting ? onlyLatest : null,
                    'excludeArchived': rerunExisting ? excludeArchived : null,
                  }),
                  child: const Text('Enable'),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      children: [
        const Text('Automatic rerun on attachment:'),
        const SizedBox(width: 12),
        Switch(
          value: issue.autoRerunEnabled,
          onChanged: (value) async {
            if (value && !issue.autoRerunEnabled) {
              // Show options dialog when enabling
              if (!context.mounted) return;
              final options = await _showAutoRerunOptionsDialog(context);
              if (options == null) return;

              if (context.mounted) {
                await ref
                    .read(issueProvider(issue.id).notifier)
                    .updateAutoRerun(
                      issueId: issue.id,
                      autoRerunEnabled: true,
                      // Only pass filter options if rerunning existing
                      autoRerunOnlyLatest: options['onlyLatest'],
                      autoRerunExcludeArchived: options['excludeArchived'],
                      rerunExisting: options['rerunExisting'],
                    );
              }
            } else {
              // Disable without dialog
              await ref.read(issueProvider(issue.id).notifier).updateAutoRerun(
                    issueId: issue.id,
                    autoRerunEnabled: false,
                  );
            }
          },
        ),
      ],
    );
  }
}
