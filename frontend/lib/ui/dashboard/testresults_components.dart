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
    final testCountText = '(${groupTestResults.length})';

    return YaruExpandable(
      header: Row(
        children: [
          testResultStatus.icon,
          const SizedBox(width: Spacing.level4),
          Text(
            testResultStatus.name,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(width: Spacing.level2),
          Text(
            testCountText,
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
            overflow: TextOverflow.ellipsis,
          ),
          const SizedBox(width: Spacing.level4),
        ],
      ),
      expandButtonPosition: YaruExpandableButtonPosition.start,
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level6),
        child: Align(
          alignment: Alignment.topLeft,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (testResult.comment != '')
                RichText(
                  textAlign: TextAlign.left,
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: 'Test Comment:',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      TextSpan(text: testResult.comment),
                    ],
                  ),
                ),
              if (testResult.ioLog != '')
                RichText(
                  textAlign: TextAlign.left,
                  text: TextSpan(
                    children: [
                      TextSpan(
                        text: 'Test IO Log:',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      TextSpan(text: testResult.ioLog),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
