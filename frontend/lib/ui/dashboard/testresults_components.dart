import 'package:flutter/material.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../models/test_results.dart';
import '../spacing.dart';

class GroupTestResultView extends StatelessWidget {
  const GroupTestResultView({
    super.key,
    required this.testResultStatus,
    required this.groupTestResults,
  });

  final List<TestResult> groupTestResults;
  final TestResultStatus testResultStatus;

  @override
  Widget build(BuildContext context) {
    return YaruExpandable(
      header: Row(
        children: [
          testResultStatus.icon,
          const SizedBox(width: Spacing.level4),
          Text(
            testResultStatus.name,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const Spacer(),
          Text(
            groupTestResults.length.toString(),
            style: Theme.of(context).textTheme.titleLarge,
          ),
        ],
      ),
      expandButtonPosition: YaruExpandableButtonPosition.start,
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level4),
        child: Column(
          children: groupTestResults
              .map(
                (testResult) => _TestResultView(testResult: testResult),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _TestResultView extends StatelessWidget {
  const _TestResultView({required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return YaruExpandable(
      header: Row(
        children: [
          testResult.status.icon,
          const SizedBox(width: Spacing.level4),
          Text(
            testResult.name,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const Spacer(),
          Text(
            'Previous results:',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(width: Spacing.level2),
          Wrap(
            alignment: WrapAlignment.start,
            children:
                testResult.historicResults.map((e) => e.reducedIcon).toList(),
          ),
        ],
      ),
      expandButtonPosition: YaruExpandableButtonPosition.start,
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level6),
        child: Wrap(
          children: [
            testResult.comment != ''
                ? Wrap(
                    children: [
                      Text(
                        'Test Comment:',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        testResult.comment,
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
            testResult.ioLog != ''
                ? Wrap(
                    alignment: WrapAlignment.start,
                    children: [
                      Text(
                        'Test IO Log:',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        testResult.ioLog,
                      ),
                    ],
                  )
                : const SizedBox.shrink(),
          ],
        ),
      ),
    );
  }
}
