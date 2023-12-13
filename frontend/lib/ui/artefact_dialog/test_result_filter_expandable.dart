import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/test_result.dart';
import '../../providers/test_results.dart';
import '../spacing.dart';

class TestResultsFilterExpandable extends ConsumerWidget {
  const TestResultsFilterExpandable({
    super.key,
    required this.statusToFilterBy,
    required this.testExecutionId,
  });

  final TestResultStatus statusToFilterBy;
  final int testExecutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testResults = ref.watch(testResultsProvider(testExecutionId));

    Color? fontColor;
    if (statusToFilterBy == TestResultStatus.failed) {
      fontColor = YaruColors.red;
    } else if (statusToFilterBy == TestResultStatus.passed) {
      fontColor = YaruColors.light.success;
    }

    final headerStyle =
        Theme.of(context).textTheme.titleMedium?.apply(color: fontColor);

    return testResults.when(
      loading: () => const Center(child: YaruCircularProgressIndicator()),
      error: (error, stackTrace) => Center(child: Text('Error: $error')),
      data: (testResults) {
        final filteredTestResults = testResults
            .filter((testResult) => testResult.status == statusToFilterBy)
            .toList();

        return YaruExpandable(
          header: Text(
            '${statusToFilterBy.name} ${filteredTestResults.length}',
            style: headerStyle,
          ),
          expandButtonPosition: YaruExpandableButtonPosition.start,
          child: Padding(
            padding: const EdgeInsets.only(left: Spacing.level5),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: filteredTestResults
                  .map(
                    (testResult) => YaruTile(title: Text(testResult.name)),
                  )
                  .toList(),
            ),
          ),
        );
      },
    );
  }
}
