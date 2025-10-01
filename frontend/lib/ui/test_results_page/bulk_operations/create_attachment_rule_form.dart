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

import '../../../models/test_results_filters.dart';
import '../../../providers/issue.dart';
import '../../../models/attachment_rule_filters.dart';
import '../../attachment_rule.dart';
import '../../issues.dart';
import '../../spacing.dart';

class _CreateAttachmentRuleForm extends ConsumerStatefulWidget {
  const _CreateAttachmentRuleForm(this.filters);

  final TestResultsFilters filters;

  @override
  ConsumerState<_CreateAttachmentRuleForm> createState() =>
      _CreateAttachmentRuleFormState();
}

class _CreateAttachmentRuleFormState
    extends ConsumerState<_CreateAttachmentRuleForm> {
  late final GlobalKey<FormState> formKey;
  String _issueUrl = '';

  @override
  void initState() {
    super.initState();
    formKey = GlobalKey<FormState>();
  }

  @override
  void dispose() {
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    if (!AttachmentRuleFilters.areFiltersCompatible(widget.filters)) {
      return Text(
        'The provided test result filters are not compatible with attachment rules.',
      );
    }
    final attachmentRuleFilters = AttachmentRuleFilters.fromTestResultsFilters(
      widget.filters,
    );
    if (!attachmentRuleFilters.hasFilters) {
      return Text(
        'Please provide at least one filter to create an attachment rule.',
      );
    }

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: Spacing.level4,
          children: [
            Text(
              'Create Attachment Rule',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            IssueUrlFormField(
              allowInternalIssue: true,
              onChanged: (value) {
                setState(() {
                  _issueUrl = value;
                });
              },
            ),
            AttachmentRuleFiltersWidget(
              filters: attachmentRuleFilters,
              editable: false,
            ),
            Row(
              children: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text(
                    'cancel',
                    style: buttonFontStyle?.apply(color: Colors.grey),
                  ),
                ),
                const Spacer(),
                TextButton(
                  key: const Key('createAttachmentRuleFormSubmitButton'),
                  onPressed: () async {
                    // Ensure the form is valid before proceeding.
                    if (formKey.currentState?.validate() != true) return;

                    // Create or get the issue.
                    final issueId = await getOrCreateIssueId(ref, _issueUrl);

                    // Create the attachment rule.
                    await ref
                        .read(issueProvider(issueId).notifier)
                        .createAttachmentRule(
                          issueId: issueId,
                          enabled: true,
                          filters: attachmentRuleFilters,
                        );

                    // Close the form.
                    if (!context.mounted) return;
                    Navigator.of(context).pop();
                  },
                  child: Text('create'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showCreateAttachmentRuleDialog({
  required BuildContext context,
  required TestResultsFilters filters,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _CreateAttachmentRuleForm(filters),
        ),
      ),
    );
