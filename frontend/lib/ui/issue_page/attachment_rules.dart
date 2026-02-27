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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dartx/dartx.dart';

import 'blinking_content.dart';

import '../../models/attachment_rule.dart';
import '../../providers/issue.dart';
import '../../routing.dart';
import '../attachment_rule.dart';
import '../expandable.dart';

class AttachmentRulesSection extends StatelessWidget {
  const AttachmentRulesSection({
    super.key,
    required this.issueId,
    required this.attachmentRules,
    this.expandRuleId,
  });

  final int issueId;
  final List<AttachmentRule> attachmentRules;
  final int? expandRuleId;

  @override
  Widget build(BuildContext context) {
    // Retrieve initially expanded attachment rule from URL
    final uri = AppRoutes.uriFromContext(context);
    final int? focusOnRuleId =
        uri.queryParameters['attachmentRule']?.toIntOrNull();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Attachment Rules',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        ...attachmentRules.map(
          (rule) => AttachmentRuleExpandable(
            issueId: issueId,
            attachmentRule: rule,
            focusOnRule: focusOnRuleId != null && rule.id == focusOnRuleId,
          ),
        ),
      ],
    );
  }
}

class AttachmentRuleExpandable extends ConsumerWidget {
  const AttachmentRuleExpandable({
    super.key,
    required this.issueId,
    required this.attachmentRule,
    this.focusOnRule = false,
  });

  final int issueId;
  final AttachmentRule attachmentRule;
  final bool focusOnRule;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return BlinkingContent(
      blink: focusOnRule,
      child: Expandable(
        initiallyExpanded: focusOnRule,
        title: Row(
          children: [
            Text('Attachment Rule #${attachmentRule.id}'),
            const Spacer(),
            TextButton(
              child: Text(attachmentRule.enabled ? 'disable' : 'enable'),
              onPressed: () async {
                if (attachmentRule.enabled) {
                  await ref
                      .read(issueProvider(issueId).notifier)
                      .disableAttachmentRule(
                        issueId: issueId,
                        attachmentRuleId: attachmentRule.id,
                      );
                } else {
                  await ref
                      .read(issueProvider(issueId).notifier)
                      .enableAttachmentRule(
                        issueId: issueId,
                        attachmentRuleId: attachmentRule.id,
                      );
                }
              },
            ),
            TextButton(
              child: Text('delete'),
              onPressed: () {
                showDialog<void>(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Delete Attachment Rule'),
                    content: const Text(
                      'Are you sure you want to delete this attachment rule?',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Cancel'),
                      ),
                      TextButton(
                        onPressed: () async {
                          await ref
                              .read(issueProvider(issueId).notifier)
                              .deleteAttachmentRule(
                                issueId: issueId,
                                attachmentRuleId: attachmentRule.id,
                              );
                          if (context.mounted) {
                            Navigator.of(context).pop();
                          }
                        },
                        child: const Text('Delete'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0),
            child: AttachmentRuleFiltersWidget(
              filters: attachmentRule.toFilters(),
              editable: false,
            ),
          ),
        ],
      ),
    );
  }
}
