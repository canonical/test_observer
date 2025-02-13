// Copyright (C) 2023-2025 Canonical Ltd.
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
import 'package:go_router/go_router.dart';

import '../../../helpers.dart';
import '../../../models/environment.dart';
import '../../../models/environment_issue.dart';
import '../../../providers/environments_issues.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_button.dart';
import '../../vanilla/vanilla_checkbox.dart';
import '../../vanilla/vanilla_modal.dart';
import '../../vanilla/vanilla_text_input.dart';

void showEnvironmentIssueUpdateDialog({
  required BuildContext context,
  required EnvironmentIssue issue,
}) =>
    showVanillaModal(
      context: context,
      builder: (_) => _EnvironmentIssueUpdateForm(issue: issue),
    );

void showEnvironmentIssueCreateDialog({
  required BuildContext context,
  required Environment environment,
}) =>
    showVanillaModal(
      context: context,
      builder: (_) => _EnvironmentIssueCreateForm(environment: environment),
    );

class _EnvironmentIssueUpdateForm extends ConsumerWidget {
  const _EnvironmentIssueUpdateForm({required this.issue});

  final EnvironmentIssue issue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _EnvironmentIssueForm(
      initialUrl: issue.url?.toString() ?? '',
      initialDescription: issue.description,
      initialIsConfirmed: issue.isConfirmed,
      formSubtitle: 'On all environments with name: ${issue.environmentName}',
      onSubmit: (url, description, isConfirmed) {
        final parsedUrl = Uri.tryParse(url);
        ref.read(environmentsIssuesProvider.notifier).updateIssue(
              issue.copyWith(
                url: (parsedUrl?.isAbsolute == true) ? parsedUrl : null,
                description: description,
                isConfirmed: isConfirmed,
              ),
            );
      },
      onDelete: () => showVanillaModal<bool>(
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
      formSubtitle: 'On all runs of environment ${environment.name}',
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
    return VanillaModal(
      title: const Text('Report Issue'),
      content: Form(
        key: _formKey,
        child: SizedBox(
          width: 700,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(widget.formSubtitle),
              const SizedBox(height: Spacing.level3),
              VanillaTextInput(
                label: 'Url',
                controller: _urlController,
                validator: (url) {
                  if ((url == null || url.isEmpty) && _isConfirmed) {
                    return 'Confirmed environment issues must have a URL';
                  }

                  if (url != null && url.isNotEmpty) {
                    return validateIssueUrl(url);
                  }

                  return null;
                },
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
                  VanillaCheckbox(
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
            ],
          ),
        ),
      ),
      actions: [
        VanillaButton(
          onPressed: () => context.pop(),
          child: const Text('cancel'),
        ),
        if (widget.onDelete != null)
          VanillaButton(
            type: VanillaButtonType.negative,
            onPressed: () {
              widget.onDelete?.call();
              context.pop();
            },
            child: const Text('delete'),
          ),
        VanillaButton(
          type: VanillaButtonType.positive,
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
          child: const Text('submit'),
        ),
      ],
    );
  }
}

class _DeleteEnvironmentIssueConfirmationDialog extends ConsumerWidget {
  const _DeleteEnvironmentIssueConfirmationDialog({required this.issue});

  final EnvironmentIssue issue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return VanillaModal(
      title: const Text('Are you sure you want to delete this issue?'),
      content: Text(
        'Note that this will remove the issue for'
        ' runs of environment ${issue.environmentName}',
      ),
      actions: [
        VanillaButton(
          onPressed: () {
            context.pop(false);
          },
          child: const Text('No'),
        ),
        VanillaButton(
          type: VanillaButtonType.negative,
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
