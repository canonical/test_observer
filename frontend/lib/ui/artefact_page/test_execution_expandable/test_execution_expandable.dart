import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_execution.dart';
import '../../../models/test_result.dart';
import '../../expandable.dart';
import '../../inline_url_text.dart';
import '../../spacing.dart';
import '../test_result_filter_expandable.dart';
import '../test_event_log_expandable.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({
    super.key,
    required this.testExecution,
    required this.runNumber,
    this.initiallyExpanded = false,
  });

  final TestExecution testExecution;
  final int runNumber;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Expandable(
      initiallyExpanded: initiallyExpanded,
      title: _TestExecutionTileTitle(
        testExecution: testExecution,
        runNumber: runNumber,
      ),
      children: <Widget>[
        TestEventLogExpandable(
          testExecutionId: testExecution.id,
          initiallyExpanded: !testExecution.status.isCompleted,
        ),
        if (testExecution.status.isCompleted)
          Expandable(
            title: const Text('Test Results'),
            initiallyExpanded: true,
            children: TestResultStatus.values
                .map(
                  (status) => TestResultsFilterExpandable(
                    statusToFilterBy: status,
                    testExecutionId: testExecution.id,
                  ),
                )
                .toList(),
          ),
      ],
    );
  }
}

class _TestExecutionTileTitle extends StatelessWidget {
  const _TestExecutionTileTitle({
    required this.testExecution,
    required this.runNumber,
  });

  final TestExecution testExecution;
  final int runNumber;

  @override
  Widget build(BuildContext context) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return Row(
      children: [
        testExecution.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          'Run $runNumber',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const Spacer(),
        if (ciLink != null)
          InlineUrlText(
            url: ciLink,
            urlText: 'CI',
          ),
        const SizedBox(width: Spacing.level3),
        if (c3Link != null)
          InlineUrlText(
            url: c3Link,
            urlText: 'C3',
          ),
      ],
    );
  }
}
