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

const possibleColors = [
  Colors.redAccent,
  Colors.yellowAccent,
  Colors.blueAccent,
  Colors.orangeAccent,
  Colors.greenAccent,
  Colors.purpleAccent,
];

class UserAvatar extends StatelessWidget {
  const UserAvatar({
    super.key,
    required this.user,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
  });

  final User user;
  final int allEnvironmentReviewsCount;
  final int completedEnvironmentReviewsCount;

  double get ratioCompleted {
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
    String result = 'Completed: $completedEnvironmentReviewsCount / '
        '$allEnvironmentReviewsCount (${(ratioCompleted * 100).round()}%)';
    if (user.isEmpty) {
      result = 'No reviewer assigned\n$result';
    } else {
      result =
          '${user.name}\n${user.launchpadHandle}\n${user.launchpadEmail}\n$result';
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
