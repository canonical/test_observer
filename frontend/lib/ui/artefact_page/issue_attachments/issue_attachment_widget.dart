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

import '../../../models/issue_attachment.dart';
import '../../../routing.dart';
import '../../spacing.dart';
import 'issue_forms/detach_issue_form.dart';
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
    final attachmentRule = issueAttachment.attachmentRule;
    return Row(
      children: [
        Expanded(
          child: IssueWidget(issue: issueAttachment.issue),
        ),
        if (attachmentRule != null) ...[
          Tooltip(
            message: attachmentRule.enabled
                ? 'Attached by an enabled attachment rule'
                : 'Attached by a disabled attachment rule',
            child: InkWell(
              onTap: () => navigateToIssuePage(
                context,
                issueAttachment.issue.id,
                attachmentRuleId: attachmentRule.id,
              ),
              child: attachmentRule.enabled
                  ? const Icon(Icons.attachment, size: 20)
                  : const Icon(Icons.link_off, size: 20, color: Colors.grey),
            ),
          ),
          SizedBox(width: Spacing.level3),
        ],
        Tooltip(
          message: 'Detach issue',
          child: TextButton(
            key: const Key('detachIssueButton'),
            child: const Text('detach'),
            onPressed: () => showDetachIssueDialog(
              context: context,
              issue: issueAttachment.issue,
              testResultId: testResultId,
              testExecutionId: testExecutionId,
            ),
          ),
        ),
      ],
    );
  }
}
