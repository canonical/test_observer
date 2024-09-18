import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../models/test_result.dart';
import '../../providers/test_results.dart';
import '../blocking_provider_preloader.dart';
import '../expandable.dart';
import 'test_result_expandable.dart';

class TestResultsFilterExpandable extends StatelessWidget {
  const TestResultsFilterExpandable({
    super.key,
    required this.statusToFilterBy,
    required this.testExecutionId,
  });

  final TestResultStatus statusToFilterBy;
  final int testExecutionId;

  @override
  Widget build(BuildContext context) {
    Color? fontColor;
    if (statusToFilterBy == TestResultStatus.failed) {
      fontColor = YaruColors.red;
    } else if (statusToFilterBy == TestResultStatus.passed) {
      fontColor = YaruColors.light.success;
    }

    final headerStyle =
        Theme.of(context).textTheme.titleMedium?.apply(color: fontColor);

    return BlockingProviderPreloader(
      provider: testResultsProvider(testExecutionId),
      builder: (_, testResults) {
        final filteredTestResults = testResults
            .filter((testResult) => testResult.status == statusToFilterBy)
            .toList();

        return Expandable(
          initiallyExpanded: statusToFilterBy == TestResultStatus.failed &&
              filteredTestResults.isNotEmpty,
          title: Text(
            '${statusToFilterBy.name} ${filteredTestResults.length}',
            style: headerStyle,
          ),
          children: filteredTestResults
              .map(
                (testResult) => TestResultExpandable(testResult: testResult),
              )
              .toList(),
        );
      },
    );
  }
}
