import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/test_execution.dart';
import '../../models/test_result.dart';
import '../inline_url_text.dart';
import '../spacing.dart';
import 'test_execution_review.dart';
import 'test_result_filter_expandable.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({super.key, required this.testExecution});

  final TestExecution testExecution;

  Row getTestExecutionTileTitle(BuildContext context) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return Row(
      children: [
        if (!testExecution.status.isCompleted) const SizedBox(width: 36.0),
        testExecution.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          testExecution.environment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        Row(
          children: [
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
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!testExecution.status.isCompleted) {
      return ListTile(
        onTap: () {},
        shape: const Border(),
        title: getTestExecutionTileTitle(context),
      );
    }

    return ExpansionTile(
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      title: getTestExecutionTileTitle(context),
      children: TestResultStatus.values
          .map(
            (status) => TestResultsFilterExpandable(
              statusToFilterBy: status,
              testExecutionId: testExecution.id,
            ),
          )
          .toList(),
    );
  }
}
