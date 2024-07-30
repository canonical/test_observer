import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_execution.dart';
import '../../../models/test_result.dart';
import '../../../providers/test_events.dart';
import '../../../providers/test_results.dart';
import '../../expandable.dart';
import '../../inline_url_text.dart';
import '../../spacing.dart';
import '../test_execution_review.dart';
import '../test_result_filter_expandable.dart';
import '../test_event_log_expandable.dart';
import 'test_execution_rerun_button.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testEvents =
        ref.watch(testEventsProvider(testExecution.id)).value ?? [];

    return _TestResultsLoader(
      testExecutionId: testExecution.id,
      child: Expandable(
        title: _TestExecutionTileTitle(
          testExecution: testExecution,
          titleAdditions: testEvents.isNotEmpty
              ? ' (${testEvents[testEvents.length - 1].eventName})'
              : '',
        ),
        children: <Widget>[
          TestEventLogExpandable(
            testExecutionId: testExecution.id,
            initiallyExpanded: !testExecution.status.isCompleted,
            testEvents: testEvents,
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
      ),
    );
  }
}

class _TestExecutionTileTitle extends StatelessWidget {
  const _TestExecutionTileTitle({
    required this.testExecution,
    required this.titleAdditions,
  });

  final TestExecution testExecution;
  final String titleAdditions;

  @override
  Widget build(BuildContext context) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return Row(
      children: [
        testExecution.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          testExecution.environment.architecture,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(width: Spacing.level4),
        Text(
          testExecution.environment.name + titleAdditions,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        RerunButton(testExecution: testExecution),
        const SizedBox(width: Spacing.level3),
        TestExecutionReviewButton(testExecution: testExecution),
        const SizedBox(width: Spacing.level4),
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

class _TestResultsLoader extends ConsumerWidget {
  const _TestResultsLoader(
      {required this.testExecutionId, required this.child});

  final int testExecutionId;
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(testResultsProvider(testExecutionId));
    return child;
  }
}
