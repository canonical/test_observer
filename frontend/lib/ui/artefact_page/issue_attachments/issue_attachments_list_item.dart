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
import 'issue_attachment_widget.dart';

class IssueAttachmentListItem extends StatelessWidget {
  const IssueAttachmentListItem({
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
    return Padding(
      padding: const EdgeInsets.symmetric(
        vertical: Spacing.level3,
        horizontal: Spacing.level4,
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          navigateToIssuePage(context, issueAttachment.issue.id);
        },
        child: Card(
          child: Padding(
            padding: const EdgeInsets.symmetric(
              vertical: Spacing.level3,
              horizontal: Spacing.level4,
            ),
            child: IssueAttachmentWidget(
              issueAttachment: issueAttachment,
              testExecutionId: testExecutionId,
              testResultId: testResultId,
            ),
          ),
        ),
      ),
    );
  }
}
