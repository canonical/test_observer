import 'package:flutter/material.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/test_execution.dart';
import '../../models/test_result.dart';
import '../inline_url_text.dart';
import '../spacing.dart';
import 'test_result_filter_expandable.dart';

class TestExecutionExpandable extends StatelessWidget {
  const TestExecutionExpandable({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
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
