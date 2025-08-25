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

import '../../../models/test_result.dart';
import '../../expandable.dart';
import 'issue_attachments_list_item.dart';
import '../../new_tag_chip.dart';
import 'issue_attachments_form.dart';
import '../../../providers/test_result_issue_attachments.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class IssueAttachmentsExpandable extends StatelessWidget {
  const IssueAttachmentsExpandable(
      {super.key, required this.testExecutionId, required this.testResult,});

  final int testExecutionId;
  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return Consumer(
      builder: (context, ref, _) {
        final attachmentsAsync = ref.watch(
          testResultIssueAttachmentsProvider(
            testExecutionId: testExecutionId,
            testResultId: testResult.id,
          ),
        );
        return attachmentsAsync.when(
          data: (attachments) => _buildExpandable(context, attachments),
          loading: () => _buildExpandable(context, testResult.issueAttachments),
          error: (e, st) => Expandable(
            initiallyExpanded: false,
            title: const Text('Test Issues (error)'),
            children: [
              Padding(
                padding: const EdgeInsets.all(16.0),
                child: Text('Failed to load issue attachments'),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildExpandable(BuildContext context, List attachments) {
    return Expandable(
      initiallyExpanded: attachments.isNotEmpty,
      title: Row(
        children: [
          Text('Test Issues (${attachments.length})'),
          const SizedBox(width: 6),
          const NewTagChip(),
          const Spacer(),
          Tooltip(
            message: 'Attach issue',
            child: TextButton(
              child: const Text('attach'),
              onPressed: () {
                showAttachIssueDialog(
                  context: context,
                  testExecutionId: testExecutionId,
                  testResult: testResult,
                );
              },
            ),
          ),
        ],
      ),
      children: attachments
          .map<Widget>(
            (attachment) => IssueAttachmentListItem(
                issueAttachment: attachment,
                testExecutionId: testExecutionId,
                testResultId: testResult.id,),
          )
          .toList(),
    );
  }
}
