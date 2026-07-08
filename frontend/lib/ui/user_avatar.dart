// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';

import '../models/user.dart';

const possibleColors = [
  Colors.redAccent,
  Colors.yellowAccent,
  Colors.blueAccent,
  Colors.orangeAccent,
  Colors.greenAccent,
  Colors.purpleAccent,
];

/// Displays a reviewer avatar with a circular progress indicator.
///
/// If both [reviewerAllCount] and [reviewerCompletedCount] are provided,
/// the progress indicator shows per-reviewer completion and the tooltip
/// displays both per-reviewer and overall statistics.
///
/// If only overall counts are provided (or if reviewer counts are partially
/// provided), the progress indicator and tooltip show overall statistics
/// across all environments.
class UserAvatar extends StatelessWidget {
  const UserAvatar({
    super.key,
    required this.user,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
    this.reviewerAllCount,
    this.reviewerCompletedCount,
  });

  final User user;
  final int allEnvironmentReviewsCount;
  final int completedEnvironmentReviewsCount;
  final int? reviewerAllCount;
  final int? reviewerCompletedCount;

  /// Whether both reviewer-specific stats are available.
  /// If only one is provided, this returns false and stats fall back to overall.
  bool get _hasReviewerStats =>
      reviewerAllCount != null && reviewerCompletedCount != null;

  double get ratioCompleted {
    if (_hasReviewerStats) {
      if (reviewerAllCount == 0) return 0.0;
      return reviewerCompletedCount! / reviewerAllCount!;
    }
    if (allEnvironmentReviewsCount == 0) {
      return 0.0;
    }
    return completedEnvironmentReviewsCount / allEnvironmentReviewsCount;
  }

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: _tooltipMessage,
      child: Stack(
        alignment: Alignment.center,
        children: [
          if (!user.isEmpty)
            CircleAvatar(
              backgroundColor: _avatarColor,
              child: Text(
                user.initials,
                style: Theme.of(context)
                    .textTheme
                    .labelLarge
                    ?.apply(fontWeightDelta: 4),
              ),
            ),
          SizedBox(
            width: 43.0,
            height: 43.0,
            child: CircularProgressIndicator(
              color: _progressColor,
              backgroundColor: _avatarColor,
              value: ratioCompleted,
              semanticsLabel: 'Circular progress indicator',
            ),
          ),
        ],
      ),
    );
  }

  String get _tooltipMessage {
    final overallRatio = allEnvironmentReviewsCount == 0
        ? 0.0
        : completedEnvironmentReviewsCount / allEnvironmentReviewsCount;
    final overallLine =
        'Overall: $completedEnvironmentReviewsCount / $allEnvironmentReviewsCount'
        ' (${(overallRatio * 100).round()}%)';

    String result;
    if (_hasReviewerStats) {
      final assignmentLine =
          'Assignments: $reviewerCompletedCount / $reviewerAllCount'
          ' (${(ratioCompleted * 100).round()}%)';
      result = '$assignmentLine\n$overallLine';
    } else {
      result = overallLine;
    }

    if (user.isEmpty) {
      result = 'No reviewer assigned\n$result';
    } else {
      if (user.launchpadHandle != null) {
        result = '${user.launchpadHandle}\n$result';
      }
      result = '${user.name}\n$result';
    }
    return result;
  }

  Color get _avatarColor => possibleColors[user.id % possibleColors.length];

  Color get _progressColor {
    final hsl = HSLColor.fromColor(_avatarColor);
    final double lightness = (hsl.lightness - 0.2).clamp(0.0, 1.0);

    return hsl.withLightness(lightness).toColor();
  }
}

class ReviewerCountAvatar extends StatelessWidget {
  const ReviewerCountAvatar({
    super.key,
    required this.reviewers,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
  });

  final List<User> reviewers;
  final int allEnvironmentReviewsCount;
  final int completedEnvironmentReviewsCount;

  double get ratioCompleted {
    if (allEnvironmentReviewsCount == 0) {
      return 0.0;
    }
    return completedEnvironmentReviewsCount / allEnvironmentReviewsCount;
  }

  String get _tooltipMessage {
    final reviewerNames = reviewers.map((r) => r.name).join('\n');
    final overallRatio = allEnvironmentReviewsCount == 0
        ? 0.0
        : completedEnvironmentReviewsCount / allEnvironmentReviewsCount;
    final overallLine =
        'Overall: $completedEnvironmentReviewsCount / $allEnvironmentReviewsCount'
        ' (${(overallRatio * 100).round()}%)';

    return '$reviewerNames\n$overallLine';
  }

  Color get _avatarColor => possibleColors[
      Object.hashAll(reviewers.map((r) => r.id)) % possibleColors.length];

  Color get _progressColor {
    final hsl = HSLColor.fromColor(_avatarColor);
    final double lightness = (hsl.lightness - 0.2).clamp(0.0, 1.0);

    return hsl.withLightness(lightness).toColor();
  }

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: _tooltipMessage,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircleAvatar(
            backgroundColor: _avatarColor,
            child: Text(
              reviewers.length.toString(),
              style: Theme.of(context)
                  .textTheme
                  .labelLarge
                  ?.apply(fontWeightDelta: 4),
            ),
          ),
          SizedBox(
            width: 43.0,
            height: 43.0,
            child: CircularProgressIndicator(
              color: _progressColor,
              backgroundColor: _avatarColor,
              value: ratioCompleted,
              semanticsLabel:
                  'Overall review progress: $completedEnvironmentReviewsCount of $allEnvironmentReviewsCount',
            ),
          ),
        ],
      ),
    );
  }
}
