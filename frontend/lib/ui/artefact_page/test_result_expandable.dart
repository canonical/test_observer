import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../models/test_result.dart';
import '../../providers/test_result_issues.dart';
import '../expandable.dart';
import 'test_issues/test_issues_expandable.dart';

class TestResultExpandable extends ConsumerWidget {
  const TestResultExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    String title = testResult.name;
    if (issues.length == 1) {
      title += ' (${issues.length} reported issue)';
    } else if (issues.length > 1) {
      title += ' (${issues.length} reported issues)';
    }

    return Expandable(
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          PreviousTestResultsWidget(
            previousResults: testResult.previousResults,
          ),
        ],
      ),
      children: [
        TestIssuesExpandable(testResult: testResult),
        _TestResultOutputExpandable(testResult: testResult),
      ],
    );
  }
}

class _TestResultOutputExpandable extends StatelessWidget {
  const _TestResultOutputExpandable({required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      title: const Text('Details'),
      initiallyExpanded: true,
      children: [
        if (testResult.category != '')
          YaruTile(
            title: const Text('Category'),
            subtitle: Text(testResult.category),
          ),
        if (testResult.comment != '')
          YaruTile(
            title: const Text('Comment'),
            subtitle: Text(testResult.comment),
          ),
        if (testResult.ioLog != '')
          YaruTile(
            title: const Text('IO Log'),
            subtitle: Text(testResult.ioLog),
          ),
      ],
    );
  }
}

class PreviousTestResultsWidget extends StatelessWidget {
  const PreviousTestResultsWidget({super.key, required this.previousResults});

  final List<PreviousTestResult> previousResults;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: previousResults
          .map(
            (e) => Tooltip(
              message: 'Version: ${e.version}',
              child: e.status.icon,
            ),
          )
          .toList(),
    );
  }
}
