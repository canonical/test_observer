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
import 'package:go_router/go_router.dart';

import '../../../providers/issues.dart';
import '../issues.dart';
import '../notification.dart';
import '../spacing.dart';

class _AddIssueForm extends ConsumerStatefulWidget {
  const _AddIssueForm();

  @override
  ConsumerState<_AddIssueForm> createState() => _AddIssueFormState();
}

class _AddIssueFormState extends ConsumerState<_AddIssueForm> {
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

    final issues = ref.watch(issuesProvider).value ?? [];
    final existingIssueIds = issues.map((issue) => issue.id).toSet();

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          spacing: Spacing.level4,
          children: [
            Text('Add Issue', style: Theme.of(context).textTheme.titleLarge),
            IssueUrlFormField(
              allowInternalIssue: false,
              onChanged: (value) {
                setState(() {
                  _issueUrl = value;
                });
              },
            ),
            Row(
              children: [
                TextButton(
                  onPressed: () => context.pop(),
                  child: Text(
                    'cancel',
                    style: buttonFontStyle?.apply(color: Colors.grey),
                  ),
                ),
                const Spacer(),
                TextButton(
                  key: const Key('addIssueFormSubmitButton'),
                  onPressed: () async {
                    // Ensure the form is valid before proceeding.
                    if (formKey.currentState?.validate() != true) return;

                    // Create or get the issue.
                    final newIssueId = await getOrCreateIssueId(ref, _issueUrl);

                    // Close the form and show a notification if the issue was
                    // already added.
                    if (!context.mounted) return;
                    if (existingIssueIds.contains(newIssueId)) {
                      showNotification(context, 'Note: Issue already added.');
                    }
                    Navigator.of(context).pop();
                  },
                  child: Text(
                    'add',
                    style: buttonFontStyle?.apply(color: Colors.black),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showAddIssueDialog({
  required BuildContext context,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _AddIssueForm(),
        ),
      ),
    );
