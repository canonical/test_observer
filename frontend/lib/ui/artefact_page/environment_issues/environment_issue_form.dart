import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../helpers.dart';
import '../../../models/environment.dart';
import '../../../models/environment_issue.dart';
import '../../../providers/environments_issues.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_text_input.dart';

void showEnvironmentIssueUpdateDialog({
  required BuildContext context,
  required EnvironmentIssue issue,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _EnvironmentIssueUpdateForm(issue: issue),
        ),
      ),
    );

void showEnvironmentIssueCreateDialog({
  required BuildContext context,
  required Environment environment,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _EnvironmentIssueCreateForm(environment: environment),
        ),
      ),
    );

class _EnvironmentIssueUpdateForm extends ConsumerWidget {
  const _EnvironmentIssueUpdateForm({required this.issue});

  final EnvironmentIssue issue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _EnvironmentIssueForm(
      initialUrl: issue.url,
      initialDescription: issue.description,
      initialIsConfirmed: issue.isConfirmed,
      formSubtitle: 'On all environments with name: ${issue.environmentName}',
      onSubmit: (url, description, isConfirmed) =>
          ref.read(environmentsIssuesProvider.notifier).updateIssue(
                issue.copyWith(
                  url: url,
                  description: description,
                  isConfirmed: isConfirmed,
                ),
              ),
      onDelete: () => showDialog<bool>(
        context: context,
        builder: (_) => _DeleteEnvironmentIssueConfirmationDialog(
          issue: issue,
        ),
      ),
    );
  }
}

class _EnvironmentIssueCreateForm extends ConsumerWidget {
  const _EnvironmentIssueCreateForm({required this.environment});

  final Environment environment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _EnvironmentIssueForm(
      formSubtitle: 'On all environments with name ${environment.name}',
      onSubmit: (url, description, isConfirmed) {
        ref.read(environmentsIssuesProvider.notifier).createIssue(
              url,
              description,
              environment.name,
              isConfirmed,
            );
      },
    );
  }
}

class _EnvironmentIssueForm extends ConsumerStatefulWidget {
  const _EnvironmentIssueForm({
    this.initialUrl = '',
    this.initialDescription = '',
    this.initialIsConfirmed = false,
    required this.formSubtitle,
    required this.onSubmit,
    this.onDelete,
  });

  final String initialUrl;
  final String initialDescription;
  final bool initialIsConfirmed;
  final String formSubtitle;
  final void Function(String url, String description, bool isConfirmed)
      onSubmit;
  final Future<bool?> Function()? onDelete;

  @override
  ConsumerState<_EnvironmentIssueForm> createState() =>
      _EnvironmentIssueFormState();
}

class _EnvironmentIssueFormState extends ConsumerState<_EnvironmentIssueForm> {
  final _formKey = GlobalKey<FormState>();
  final _urlController = TextEditingController();
  final _descriptionController = TextEditingController();
  late bool _isConfirmed;

  @override
  void initState() {
    super.initState();
    _urlController.text = widget.initialUrl;
    _descriptionController.text = widget.initialDescription;
    _isConfirmed = widget.initialIsConfirmed;
  }

  @override
  void dispose() {
    _urlController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    return Form(
      key: _formKey,
      child: SizedBox(
        width: 700,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Report Issue', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: Spacing.level4),
            Text(widget.formSubtitle),
            const SizedBox(height: Spacing.level3),
            VanillaTextInput(
              label: 'Url',
              controller: _urlController,
              validator: validateIssueUrl,
            ),
            const SizedBox(height: Spacing.level3),
            VanillaTextInput(
              label: 'Description',
              multiline: true,
              controller: _descriptionController,
              validator: (url) => url == null || url.isEmpty
                  ? 'Must provide a description of the issue'
                  : null,
            ),
            const SizedBox(height: Spacing.level4),
            Row(
              children: [
                const Text('Needs confirmation'),
                const SizedBox(width: Spacing.level2),
                Checkbox(
                  value: !_isConfirmed,
                  onChanged: (value) {
                    if (value != null) {
                      setState(() {
                        _isConfirmed = !value;
                      });
                    }
                  },
                ),
                const SizedBox(width: Spacing.level2),
                Text(
                  '(Does this issue require certlab\'s confirmation?)',
                  style: Theme.of(context)
                      .textTheme
                      .bodyMedium
                      ?.copyWith(color: Colors.grey),
                ),
              ],
            ),
            const SizedBox(height: Spacing.level4),
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
                if (widget.onDelete != null)
                  TextButton(
                    onPressed: () {
                      widget.onDelete
                          ?.call()
                          .then((didDelete) => context.pop());
                    },
                    child: Text(
                      'delete',
                      style: buttonFontStyle?.apply(color: Colors.red),
                    ),
                  ),
                TextButton(
                  onPressed: () {
                    if (_formKey.currentState?.validate() == true) {
                      widget.onSubmit(
                        _urlController.text,
                        _descriptionController.text,
                        _isConfirmed,
                      );
                      context.pop();
                    }
                  },
                  child: Text(
                    'submit',
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

class _DeleteEnvironmentIssueConfirmationDialog extends ConsumerWidget {
  const _DeleteEnvironmentIssueConfirmationDialog({required this.issue});

  final EnvironmentIssue issue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AlertDialog(
      title: const Text('Are you sure you want to delete this issue?'),
      content: Text(
        'Note that this will remove the issue for'
        ' runs of environment ${issue.environmentName}',
      ),
      actions: [
        TextButton(
          onPressed: () {
            context.pop(false);
          },
          child: const Text('No'),
        ),
        TextButton(
          onPressed: () {
            ref.read(environmentsIssuesProvider.notifier).deleteIssue(issue.id);
            context.pop(true);
          },
          child: const Text('Yes'),
        ),
      ],
    );
  }
}
