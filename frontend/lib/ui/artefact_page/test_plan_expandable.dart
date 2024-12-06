import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';

import '../../models/test_execution.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'test_execution_expandable/test_execution_expandable.dart';
import 'test_execution_expandable/test_execution_rerun_button.dart';

class TestPlanExpandable extends StatelessWidget {
  const TestPlanExpandable({
    super.key,
    required this.testExecutionsDescending,
    this.initiallyExpanded = false,
  });

  final bool initiallyExpanded;
  final Iterable<TestExecution> testExecutionsDescending;

  @override
  Widget build(BuildContext context) {
    String title = testExecutionsDescending.first.testPlan;
    if (title.isEmpty) {
      title = 'Unknown';
    }

    return Expandable(
      initiallyExpanded: initiallyExpanded,
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          RerunButton(testExecution: testExecutionsDescending.first),
          const SizedBox(width: Spacing.level3),
        ],
      ),
      children: testExecutionsDescending
          .mapIndexed(
            (i, te) => TestExecutionExpandable(
              initiallyExpanded: i == 0,
              testExecution: te,
              runNumber: testExecutionsDescending.length - i,
            ),
          )
          .toList(),
    );
  }
}
