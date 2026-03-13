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

import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../../models/test_results_filters.dart';
import '../../spacing.dart';
import 'bulk_issue_attachment_form.dart';
import 'create_attachment_rule_form.dart';
import 'bulk_modify_reruns_form.dart';

enum BulkOperationType {
  createAttachmentRule,
  attachIssue,
  detachIssue,
  createRerunRequests,
  deleteRerunRequests,
}

class BulkOperationsButtons extends StatelessWidget {
  final TestResultsFilters filters;
  final bool disabled;
  final Set<BulkOperationType>? enabledOperations;

  const BulkOperationsButtons({
    super.key,
    required this.filters,
    this.disabled = false,
    this.enabledOperations,
  });

  bool _isOperationEnabled(BulkOperationType operation) {
    return enabledOperations == null || enabledOperations!.contains(operation);
  }

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
            if (_isOperationEnabled(BulkOperationType.createAttachmentRule))
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
            if (_isOperationEnabled(BulkOperationType.attachIssue))
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
            if (_isOperationEnabled(BulkOperationType.detachIssue))
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
            if (_isOperationEnabled(BulkOperationType.createRerunRequests))
              ElevatedButton(
                onPressed: disabled
                    ? null
                    : () => showModifyRerunsDialog(
                          context: context,
                          filters: filters,
                          shouldDelete: false,
                        ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: YaruColors.orange,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Create Rerun Requests'),
              ),
            if (_isOperationEnabled(BulkOperationType.deleteRerunRequests))
              ElevatedButton(
                onPressed: disabled
                    ? null
                    : () => showModifyRerunsDialog(
                          context: context,
                          filters: filters,
                          shouldDelete: true,
                        ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: YaruColors.orange,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Delete Rerun Requests'),
              ),
          ],
        ),
      ],
    );
  }
}
