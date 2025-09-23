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
import 'package:yaru/yaru.dart';

import '../../../../models/attachment_rule_filters.dart';
import '../../../../models/test_results_filters.dart';
import '../../../../providers/test_results_search.dart';
import '../../../inline_url_text.dart';
import '../../../spacing.dart';

class BulkAttachSection extends ConsumerWidget {
  const BulkAttachSection({
    super.key,
    required this.splitTime,
    required this.attachmentRuleFilters,
    required this.selectedBulkAttachOlder,
    required this.selectedBulkAttachNewer,
    required this.onBulkAttachOlderChanged,
    required this.onBulkAttachNewerChanged,
  });

  final DateTime splitTime;
  final AttachmentRuleFilters attachmentRuleFilters;
  final bool selectedBulkAttachOlder;
  final bool selectedBulkAttachNewer;
  final ValueChanged<bool> onBulkAttachOlderChanged;
  final ValueChanged<bool> onBulkAttachNewerChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Attach to existing test results',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        _BulkAttachIssueOption(
          title: 'Older test results',
          value: selectedBulkAttachOlder,
          filters: attachmentRuleFilters.toTestResultsFilters().copyWith(
                untilDate: splitTime,
              ),
          loadNumberResults: attachmentRuleFilters.hasFilters,
          onChanged: onBulkAttachOlderChanged,
        ),
        _BulkAttachIssueOption(
          title: 'Newer test results',
          value: selectedBulkAttachNewer,
          filters: attachmentRuleFilters.toTestResultsFilters().copyWith(
                fromDate: splitTime,
              ),
          loadNumberResults: attachmentRuleFilters.hasFilters,
          onChanged: onBulkAttachNewerChanged,
        ),
      ],
    );
  }
}

class _BulkAttachIssueOption extends ConsumerWidget {
  const _BulkAttachIssueOption({
    required this.title,
    required this.value,
    required this.filters,
    this.loadNumberResults = false,
    required this.onChanged,
  });

  final String title;
  final bool value;
  final TestResultsFilters filters;
  final bool loadNumberResults;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final matchingTestResults = loadNumberResults
        ? ref.watch(testResultsSearchProvider(filters.copyWith(limit: 0)))
        : null;
    return CheckboxListTile(
      title: Row(
        spacing: Spacing.level3,
        children: [
          Text(title),
          if (loadNumberResults)
            matchingTestResults!.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: YaruCircularProgressIndicator(),
                  )
                : InlineUrlText(
                    url: '/#${filters.toTestResultsUri()}',
                    urlText:
                        'Matches ${matchingTestResults.value?.count ?? 0} test results',
                    fontStyle: DefaultTextStyle.of(context).style.apply(
                          color: Theme.of(context).colorScheme.primary,
                          fontStyle: FontStyle.italic,
                          decoration: TextDecoration.none,
                        ),
                  ),
        ],
      ),
      value: value,
      onChanged: (selected) {
        onChanged(selected ?? false);
      },
    );
  }
}
