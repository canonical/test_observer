// Copyright (C) 2023 Canonical Ltd.
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

import '../models/user.dart';
import 'user_avatar.dart';

class ReviewersAvatars extends StatelessWidget {
  const ReviewersAvatars({
    super.key,
    required this.reviewers,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
  });

  final List<User> reviewers;
  final int allEnvironmentReviewsCount;
  final int completedEnvironmentReviewsCount;

  @override
  Widget build(BuildContext context) {
    if (reviewers.isEmpty) {
      // Show single empty avatar if no reviewers
      return UserAvatar(
        user: emptyUser,
        allEnvironmentReviewsCount: allEnvironmentReviewsCount,
        completedEnvironmentReviewsCount: completedEnvironmentReviewsCount,
      );
    }

    if (reviewers.length == 1) {
      // Show single avatar for one reviewer
      return UserAvatar(
        user: reviewers.first,
        allEnvironmentReviewsCount: allEnvironmentReviewsCount,
        completedEnvironmentReviewsCount: completedEnvironmentReviewsCount,
      );
    }

    // Show stacked avatars for multiple reviewers
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (int i = 0; i < reviewers.length; i++)
          Transform.translate(
            offset: Offset(-8.0 * i, 0),
            child: UserAvatar(
              user: reviewers[i],
              allEnvironmentReviewsCount: allEnvironmentReviewsCount,
              completedEnvironmentReviewsCount: completedEnvironmentReviewsCount,
            ),
          ),
      ],
    );
  }
}
