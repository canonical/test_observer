import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_result.dart';
import '../../../providers/test_result_issues.dart';
import '../../expandable.dart';
import 'test_issue_form.dart';
import 'test_issue_list_item.dart';

class TestIssuesExpandable extends ConsumerWidget {
  const TestIssuesExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    return Expandable(
      initiallyExpanded: issues.isNotEmpty,
      title: Row(
        children: [
          Text('Reported Issues (${issues.length})'),
          const Spacer(),
          TextButton(
            onPressed: () => showTestIssueCreateDialog(
              context: context,
              testResult: testResult,
            ),
            child: const Text('add'),
          ),
        ],
      ),
      children: issues.map((issue) => TestIssueListItem(issue: issue)).toList(),
    );
  }
}
