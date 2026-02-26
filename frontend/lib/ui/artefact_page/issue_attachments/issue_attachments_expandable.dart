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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../../providers/test_results.dart';
import '../../expandable.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_chip.dart';
import 'issue_attachments_list_item.dart';
import 'issue_forms/attach_issue_form.dart';

class IssueAttachmentsExpandable extends ConsumerWidget {
  const IssueAttachmentsExpandable({
    super.key,
    required this.testExecutionId,
    required this.testResultId,
    required this.artefactId,
    this.initiallyExpanded,
  });

  final int testExecutionId;
  final int testResultId;
  final int artefactId;
  final bool? initiallyExpanded;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final attachmentsAsync = ref.watch(
      testResultsProvider(testExecutionId).select(
        (value) => value.whenData(
          (results) => results
              .firstWhere((result) => result.id == testResultId)
              .issueAttachments,
        ),
      ),
    );
    if (attachmentsAsync.isLoading) {
      return const CircularProgressIndicator();
    }
    final attachments = attachmentsAsync.value ?? [];
    return Expandable(
      initiallyExpanded: initiallyExpanded ?? attachments.isNotEmpty,
      title: Row(
        spacing: Spacing.level2,
        children: [
          Text('Test Issues (${attachments.length})'),
          Tooltip(
            message: 'Learn more',
            child: IconButton(
              icon: const Icon(Icons.info_outline),
              onPressed: () => launchUrlString(
                'https://canonical-test-observer.readthedocs-hosted.com/en/latest/how-to/triage-test-results/',
              ),
            ),
          ),
          const VanillaChip(
            text: 'NEW',
            fontColor: Colors.white,
            backgroundColor: Colors.blue,
            side: BorderSide.none,
          ),
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
                  artefactId: artefactId,
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
