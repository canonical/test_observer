import 'package:flutter/material.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/test_result.dart';
import '../spacing.dart';

class TestResultExpandable extends StatelessWidget {
  const TestResultExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return YaruExpandable(
      expandButtonPosition: YaruExpandableButtonPosition.start,
      header: Row(
        children: [
          Text(testResult.name),
          const Spacer(),
          PreviousTestResultsWidget(
            previousResults: testResult.previousResults,
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level5),
        child: Column(
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
        ),
      ),
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
