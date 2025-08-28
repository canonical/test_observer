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

import '../../../providers/test_result_issue_attachments.dart';
import '../../expandable.dart';
import '../../new_tag_chip.dart';
import 'issue_attachments_form.dart';
import 'issue_attachments_list_item.dart';

class IssueAttachmentsExpandable extends ConsumerWidget {
  const IssueAttachmentsExpandable({
    super.key,
    required this.testExecutionId,
    required this.testResultId,
  });

  final int testExecutionId;
  final int testResultId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final attachmentsAsync = ref.watch(
      testResultIssueAttachmentsProvider(
        testExecutionId: testExecutionId,
        testResultId: testResultId,
      ),
    );
    if (attachmentsAsync.isLoading) {
      return const CircularProgressIndicator();
    }
    final attachments = attachmentsAsync.value ?? [];
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
              key: const Key('attachIssueButton'),
              child: const Text('attach'),
              onPressed: () {
                showAttachIssueDialog(
                  context: context,
                  testExecutionId: testExecutionId,
                  testResultId: testResultId,
                );
              },
            ),
          ),
        ],
      ),
      children: attachments
          .map(
            (attachment) => IssueAttachmentListItem(
              issueAttachment: attachment,
              testExecutionId: testExecutionId,
              testResultId: testResultId,
            ),
          )
          .toList(),
    );
  }
}
