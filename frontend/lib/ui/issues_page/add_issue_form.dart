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
import '../notification.dart';
import '../spacing.dart';
import '../vanilla/vanilla_text_input.dart';

class _AddIssueForm extends ConsumerStatefulWidget {
  const _AddIssueForm();

  @override
  ConsumerState<_AddIssueForm> createState() => _AddIssueFormState();
}

class _AddIssueFormState extends ConsumerState<_AddIssueForm> {
  late final GlobalKey<FormState> formKey;
  late final TextEditingController urlController;

  @override
  void initState() {
    super.initState();
    formKey = GlobalKey<FormState>();
    urlController = TextEditingController();
  }

  @override
  void dispose() {
    urlController.dispose();
    super.dispose();
  }

  String? _validateUrl(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a URL';
    }
    final uri = Uri.tryParse(value);
    if (uri == null || !uri.hasScheme || !uri.hasAuthority) {
      return 'Please enter a valid URL';
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    final issues = ref.watch(issuesProvider).value ?? [];

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Add Issue', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: Spacing.level4),
            VanillaTextInput(
              key: const Key('addIssueFormUrlInput'),
              label: 'External issue URL (GitHub, Jira, Launchpad)',
              controller: urlController,
              validator: (value) => _validateUrl(value),
            ),
            const SizedBox(height: Spacing.level3),
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
                    if (formKey.currentState?.validate() != true) return;
                    final url = urlController.text.trim();
                    final existingIssueIds =
                        issues.map((issue) => issue.id).toSet();
                    final newIssue = await ref
                        .read(issuesProvider.notifier)
                        .createIssue(url: url);
                    if (!context.mounted) return;
                    if (existingIssueIds.contains(newIssue.id)) {
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
