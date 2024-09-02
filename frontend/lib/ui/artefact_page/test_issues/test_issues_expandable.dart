import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_result.dart';
import '../../../providers/tests_issues.dart';
import '../../expandable.dart';

class TestIssuesExpandable extends ConsumerWidget {
  const TestIssuesExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref
            .watch(
              testsIssuesProvider.select(
                (value) => value.whenData(
                  (issues) => issues.filter(
                    (issue) =>
                        issue.caseName == testResult.name ||
                        issue.templateId == testResult.templateId,
                  ),
                ),
              ),
            )
            .value ??
        [];
    return Expandable(
      title: const Text('Reported Issues'),
      children: issues.map((issue) => Text(issue.description)).toList(),
    );
  }
}
