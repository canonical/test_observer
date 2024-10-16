import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';
import 'package:popover/popover.dart';

import '../../models/environment_review.dart';
import '../../routing.dart';
import 'environment_review_pop_over.dart';

class EnvironmentReviewButton extends StatelessWidget {
  const EnvironmentReviewButton({super.key, required this.environmentReview});

  final EnvironmentReview environmentReview;

  Text _getReviewDecisionText(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    if (environmentReview.reviewDecision.isEmpty) {
      return Text(
        'Undecided',
        style: fontStyle?.apply(color: YaruColors.textGrey),
      );
    } else if (environmentReview.reviewDecision
        .contains(EnvironmentReviewDecision.rejected)) {
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
          bodyBuilder: (context) => EnvironmentReviewPopOver(
            artefactId: artefactId,
            environmentReview: environmentReview,
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
