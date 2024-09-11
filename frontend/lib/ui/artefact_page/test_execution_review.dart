import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';
import 'package:popover/popover.dart';

import '../../models/test_execution.dart';
import '../../routing.dart';
import 'test_execution_pop_over.dart';

class TestExecutionReviewButton extends StatelessWidget {
  const TestExecutionReviewButton({
    super.key,
    required this.testExecution,
  });

  final TestExecution testExecution;

  Text _getReviewDecisionText(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    if (testExecution.reviewDecision.isEmpty) {
      return Text(
        'Undecided',
        style: fontStyle?.apply(color: YaruColors.textGrey),
      );
    } else if (testExecution.reviewDecision
        .contains(TestExecutionReviewDecision.rejected)) {
      return Text(
        'Rejected',
        style: fontStyle?.apply(color: YaruColors.red),
      );
    } else {
      return Text(
        'Approved',
        style: fontStyle?.apply(color: YaruColors.light.success),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));
    return GestureDetector(
      onTap: () {
        showPopover(
          context: context,
          bodyBuilder: (context) => TestExecutionPopOver(
            testExecution: testExecution,
            artefactId: artefactId,
          ),
          direction: PopoverDirection.bottom,
          width: 500,
          height: 450,
          arrowHeight: 15,
          arrowWidth: 30,
        );
      },
      child: Chip(
        label: _getReviewDecisionText(context),
        shape: const StadiumBorder(),
      ),
    );
  }
}
