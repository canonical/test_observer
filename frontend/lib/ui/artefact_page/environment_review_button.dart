// Copyright (C) 2023-2025 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
