import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/environment_review.dart';
import '../../../models/test_execution.dart';
import '../../../models/test_result.dart';
import '../../expandable.dart';
import '../../inline_url_text.dart';
import '../../spacing.dart';
import '../environment_issues/environment_issues_expandable.dart';
import '../environment_review_button.dart';
import '../test_result_filter_expandable.dart';
import '../test_event_log_expandable.dart';
import 'test_execution_rerun_button.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({
    super.key,
    required this.testExecution,
    required this.environmentReview,
  });

  final TestExecution testExecution;
  final EnvironmentReview environmentReview;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Expandable(
      title: _TestExecutionTileTitle(
        testExecution: testExecution,
        environmentReview: environmentReview,
      ),
      children: <Widget>[
        EnvironmentIssuesExpandable(environment: testExecution.environment),
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
    required this.environmentReview,
  });

  final TestExecution testExecution;
  final EnvironmentReview environmentReview;

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
          testExecution.environment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        RerunButton(testExecution: testExecution),
        const SizedBox(width: Spacing.level3),
        EnvironmentReviewButton(environmentReview: environmentReview),
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
