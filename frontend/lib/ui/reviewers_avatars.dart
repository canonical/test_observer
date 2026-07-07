// Copyright 2023 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';

import '../models/environment_review.dart';
import '../models/user.dart';
import 'user_avatar.dart';

class ReviewersAvatars extends StatelessWidget {
  const ReviewersAvatars({
    super.key,
    required this.reviewers,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
    this.environmentReviews = const [],
  });

  final List<User> reviewers;
  final int allEnvironmentReviewsCount;
  final int completedEnvironmentReviewsCount;
  final List<EnvironmentReview> environmentReviews;

  /// Returns a map from user id to (all, completed) assignment counts
  /// derived from [environmentReviews]. When [environmentReviews] is empty
  /// the map is empty and callers fall back to the overall artefact counts.
  Map<int, ({int all, int completed})> get _reviewerStats {
    if (environmentReviews.isEmpty) return {};
    final stats = <int, ({int all, int completed})>{};
    for (final review in environmentReviews) {
      final isCompleted = review.reviewDecision.isNotEmpty;
      for (final reviewer in review.reviewers) {
        final current = stats[reviewer.id] ?? (all: 0, completed: 0);
        stats[reviewer.id] = (
          all: current.all + 1,
          completed: current.completed + (isCompleted ? 1 : 0),
        );
      }
    }
    return stats;
  }

  @override
  Widget build(BuildContext context) {
    final stats = _reviewerStats;

    UserAvatar buildUserAvatar(User user) {
      final s = stats[user.id];
      return UserAvatar(
        user: user,
        allEnvironmentReviewsCount: allEnvironmentReviewsCount,
        completedEnvironmentReviewsCount: completedEnvironmentReviewsCount,
        reviewerAllCount: s?.all,
        reviewerCompletedCount: s?.completed,
      );
    }

    if (reviewers.isEmpty) {
      // Show single empty avatar if no reviewers
      return UserAvatar(
        user: emptyUser,
        allEnvironmentReviewsCount: allEnvironmentReviewsCount,
        completedEnvironmentReviewsCount: completedEnvironmentReviewsCount,
      );
    }

    if (reviewers.length == 1) {
      return buildUserAvatar(reviewers.first);
    }

    // Show stacked avatars for multiple reviewers
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (int i = 0; i < reviewers.length; i++)
          Transform.translate(
            offset: Offset(-8.0 * i, 0),
            child: buildUserAvatar(reviewers[i]),
          ),
      ],
    );
  }
}
