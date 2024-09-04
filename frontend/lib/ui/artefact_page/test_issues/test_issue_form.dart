import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../models/test_issue.dart';
import '../../../models/test_result.dart';
import '../../../providers/tests_issues.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_text_input.dart';

void showTestIssueUpdateDialog({
  required BuildContext context,
  required TestIssue issue,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _TestIssueUpdateForm(issue: issue),
        ),
      ),
    );

void showTestIssueCreateDialog({
  required BuildContext context,
  required TestResult testResult,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _TestIssueCreateForm(testResult: testResult),
        ),
      ),
    );

class _TestIssueUpdateForm extends ConsumerWidget {
  const _TestIssueUpdateForm({required this.issue});

  final TestIssue issue;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issueOn = issue.templateId.isEmpty
        ? 'On all cases with name: ${issue.caseName}'
        : 'On all cases with template id: ${issue.templateId}';
    return _TestIssueForm(
      initialUrl: issue.url,
      initialDescription: issue.description,
      formSubtitle: issueOn,
      onSubmit: (url, description) =>
          ref.read(testsIssuesProvider.notifier).updateIssue(
                issue.copyWith(
                  url: url,
                  description: description,
                ),
              ),
      onDelete: () =>
          ref.read(testsIssuesProvider.notifier).deleteIssue(issue.id),
    );
  }
}

class _TestIssueCreateForm extends ConsumerWidget {
  const _TestIssueCreateForm({required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issueOn = testResult.templateId.isEmpty
        ? 'On all cases with name: ${testResult.name}'
        : 'On all cases with template id: ${testResult.templateId}';
    return _TestIssueForm(
      formSubtitle: issueOn,
      onSubmit: (url, description) {
        if (testResult.templateId.isEmpty) {
          ref.read(testsIssuesProvider.notifier).createIssue(
                url,
                description,
                caseName: testResult.name,
              );
        } else {
          ref.read(testsIssuesProvider.notifier).createIssue(
                url,
                description,
                templateId: testResult.templateId,
              );
        }
      },
    );
  }
}

class _TestIssueForm extends ConsumerStatefulWidget {
  const _TestIssueForm({
    this.initialUrl = '',
    this.initialDescription = '',
    required this.formSubtitle,
    required this.onSubmit,
    this.onDelete,
  });

  final String initialUrl;
  final String initialDescription;
  final String formSubtitle;
  final void Function(String url, String description) onSubmit;
  final void Function()? onDelete;

  @override
  ConsumerState<_TestIssueForm> createState() => _TestIssueFormState();
}

class _TestIssueFormState extends ConsumerState<_TestIssueForm> {
  final _formKey = GlobalKey<FormState>();
  final _urlController = TextEditingController();
  final _descriptionController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _urlController.text = widget.initialUrl;
    _descriptionController.text = widget.initialDescription;
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
              validator: (url) {
                if (url == null || url.isEmpty) {
                  return 'Must provide a bug/jira link to the issue';
                }
                if (Uri.tryParse(url) == null) {
                  return 'Provided url is not valid';
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
                      showDialog(
                        context: context,
                        builder: (_) => _DeleteTestIssueConfirmationDialog(
                            onDelete: widget.onDelete!),
                      );
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

class _DeleteTestIssueConfirmationDialog extends StatelessWidget {
  const _DeleteTestIssueConfirmationDialog({required this.onDelete});

  final void Function() onDelete;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Are you sure you want to delete this issue?'),
      content: const Text(
        'Note that this will remove the issue for all related tests',
      ),
      actions: [
        TextButton(
          onPressed: () {
            context.pop();
          },
          child: const Text('No'),
        ),
        TextButton(
          onPressed: () {
            onDelete();
            context.pop();
            context.pop();
          },
          child: const Text('Yes'),
        ),
      ],
    );
  }
}
