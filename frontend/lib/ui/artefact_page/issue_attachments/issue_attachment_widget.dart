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

import '../../../models/issue_attachment.dart';
import '../../spacing.dart';
import 'issue_attachments_form.dart';
import 'issue_widget.dart';

class IssueAttachmentWidget extends StatelessWidget {
  const IssueAttachmentWidget({
    super.key,
    required this.issueAttachment,
    required this.testExecutionId,
    required this.testResultId,
  });

  final IssueAttachment issueAttachment;
  final int testExecutionId;
  final int testResultId;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: IssueWidget(issue: issueAttachment.issue),
        ),
        if (issueAttachment.attachmentRule != null) ...[
          Tooltip(
            message: 'Attached by a rule',
            child: InkWell(
              onTap: () {}, // Placeholder link
              child: const Icon(Icons.attachment, size: 20),
            ),
          ),
          SizedBox(width: Spacing.level3),
        ],
        Tooltip(
          message: 'Detach issue',
          child: TextButton(
            key: const Key('detachIssueButton'),
            child: const Text('detach'),
            onPressed: () {
              showDetachIssueDialog(
                context: context,
                issue: issueAttachment.issue,
                testResultId: testResultId,
                testExecutionId: testExecutionId,
              );
            },
          ),
        ),
      ],
    );
  }
}
