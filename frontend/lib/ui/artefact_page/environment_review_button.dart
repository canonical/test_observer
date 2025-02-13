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
import 'package:popover/popover.dart';

import '../../models/environment_review.dart';
import '../../routing.dart';
import '../vanilla/vanilla_chip.dart';
import 'environment_review_pop_over.dart';

class EnvironmentReviewButton extends StatelessWidget {
  const EnvironmentReviewButton({super.key, required this.environmentReview});

  final EnvironmentReview environmentReview;

  VanillaChip _getReviewDecisionWidget() {
    if (environmentReview.reviewDecision.isEmpty) {
      return const VanillaChip(text: 'Undecided');
    } else if (environmentReview.reviewDecision
        .contains(EnvironmentReviewDecision.rejected)) {
      return const VanillaChip(
        text: 'Rejected',
        type: VanillaChipType.negative,
      );
    } else {
      return const VanillaChip(
        text: 'Approved',
        type: VanillaChipType.positive,
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
      child: _getReviewDecisionWidget(),
    );
  }
}
