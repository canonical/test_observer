import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../models/test_issue.dart';
import '../../../providers/tests_issues.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_text_input.dart';

class TestIssueForm extends ConsumerStatefulWidget {
  const TestIssueForm({super.key, required this.issue});

  final TestIssue issue;

  @override
  ConsumerState<TestIssueForm> createState() => _TestIssueFormState();
}

class _TestIssueFormState extends ConsumerState<TestIssueForm> {
  final urlController = TextEditingController();
  final descriptionController = TextEditingController();

  @override
  void initState() {
    super.initState();
    urlController.text = widget.issue.url;
    descriptionController.text = widget.issue.description;
  }

  @override
  void dispose() {
    urlController.dispose();
    descriptionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final issueOn = widget.issue.templateId.isEmpty
        ? 'On all cases with name: ${widget.issue.caseName}'
        : 'On all cases with template id: ${widget.issue.templateId}';

    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;

    return SizedBox(
      width: 700,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Report Issue', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: Spacing.level4),
          Text(issueOn),
          const SizedBox(height: Spacing.level3),
          VanillaTextInput(label: 'Url', controller: urlController),
          const SizedBox(height: Spacing.level3),
          VanillaTextInput(
            label: 'Description',
            multiline: true,
            controller: descriptionController,
          ),
          const SizedBox(height: Spacing.level4),
          Row(
            children: [
              TextButton(
                onPressed: () {
                  context.pop();
                },
                child: Text(
                  'cancel',
                  style: buttonFontStyle?.apply(color: Colors.grey),
                ),
              ),
              const Spacer(),
              TextButton(
                onPressed: () {
                  context.pop();
                },
                child: Text(
                  'delete',
                  style: buttonFontStyle?.apply(color: Colors.red),
                ),
              ),
              TextButton(
                onPressed: () {
                  ref.read(testsIssuesProvider.notifier).updateIssue(
                        widget.issue.copyWith(
                          url: urlController.text,
                          description: descriptionController.text,
                        ),
                      );
                  context.pop();
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
    );
  }
}

void showTestIssueDialog({
  required BuildContext context,
  required int issueId,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: Consumer(
            builder: (context, ref, child) {
              final issue = ref
                  .watch(
                    testsIssuesProvider.select(
                      (value) => value.whenData(
                        (issues) =>
                            issues.firstWhere((issue) => issue.id == issueId),
                      ),
                    ),
                  )
                  .requireValue;
              return TestIssueForm(issue: issue);
            },
          ),
        ),
      ),
    );
