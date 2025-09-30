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
import 'package:yaru/yaru.dart';

import '../../../models/test_results_filters.dart';
import '../../spacing.dart';
import 'bulk_issue_attachment_form.dart';
import 'create_attachment_rule_form.dart';

class BulkOperationsButtons extends StatelessWidget {
  final TestResultsFilters filters;
  final bool disabled;

  const BulkOperationsButtons({
    super.key,
    required this.filters,
    this.disabled = false,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: Spacing.level3,
      children: [
        Text(
          'Bulk Operations',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.start,
          spacing: Spacing.level4,
          runSpacing: Spacing.level4,
          children: [
            ElevatedButton(
              onPressed: disabled
                  ? null
                  : () => showCreateAttachmentRuleDialog(
                        context: context,
                        filters: filters,
                      ),
              style: ElevatedButton.styleFrom(
                backgroundColor: YaruColors.orange,
                foregroundColor: Colors.white,
              ),
              child: const Text('Create Attachment Rule'),
            ),
            ElevatedButton(
              onPressed: disabled
                  ? null
                  : () => showBulkIssueAttachmentDialog(
                        context: context,
                        filters: filters,
                        shouldDetach: false,
                      ),
              style: ElevatedButton.styleFrom(
                backgroundColor: YaruColors.orange,
                foregroundColor: Colors.white,
              ),
              child: const Text('Attach Issue'),
            ),
            ElevatedButton(
              onPressed: disabled
                  ? null
                  : () => showBulkIssueAttachmentDialog(
                        context: context,
                        filters: filters,
                        shouldDetach: true,
                      ),
              style: ElevatedButton.styleFrom(
                backgroundColor: YaruColors.orange,
                foregroundColor: Colors.white,
              ),
              child: const Text('Detach Issue'),
            ),
          ],
        ),
      ],
    );
  }
}
