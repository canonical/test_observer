import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/test_execution.dart';
import '../../models/test_result.dart';
import '../inline_url_text.dart';
import '../spacing.dart';
import 'test_execution_review.dart';
import 'test_result_filter_expandable.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({
    super.key,
    required this.testExecution,
    required this.artefactId,
  });

  final TestExecution testExecution;
  final int artefactId;

  Chip getStatusChip(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    if (testExecution.reviewDecision.isEmpty) {
      return Chip(
        label: Text(
          'Undecided',
          style: fontStyle?.apply(color: YaruColors.textGrey),
        ),
        shape: const StadiumBorder(),
      );
    } else if (testExecution.reviewDecision
        .contains(TestExecutionReviewDecision.rejected)) {
      return Chip(
        label: Text(
          'Rejected',
          style: fontStyle?.apply(color: YaruColors.red),
        ),
        shape: const StadiumBorder(),
      );
    } else {
      return Chip(
        label: Text(
          'Approved',
          style: fontStyle?.apply(color: YaruColors.light.success),
        ),
        shape: const StadiumBorder(),
      );
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return YaruExpandable(
      header: Row(
        children: [
          testExecution.status.icon,
          const SizedBox(width: Spacing.level4),
          Text(
            testExecution.environment.name,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const Spacer(),
          getStatusChip(context),
          TestExecutionReviewButton(
            testExecution: testExecution,
            artefactId: artefactId,
          ),
          Row(
            children: [
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
      ),
      expandButtonPosition: YaruExpandableButtonPosition.start,
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level4),
        child: Column(
          children: TestResultStatus.values
              .map(
                (status) => TestResultsFilterExpandable(
                  statusToFilterBy: status,
                  testExecutionId: testExecution.id,
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}
