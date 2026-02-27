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

import '../../models/user.dart';
import '../user_avatar.dart';

class EnvironmentReviewersAvatars extends StatelessWidget {
  const EnvironmentReviewersAvatars({
    super.key,
    required this.reviewers,
  });

  final List<User> reviewers;

  @override
  Widget build(BuildContext context) {
    if (reviewers.isEmpty) {
      return const SizedBox.shrink();
    }

    if (reviewers.length == 1) {
      return _SimpleUserAvatar(user: reviewers.first);
    }

    // Show stacked avatars for multiple reviewers
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        for (int i = 0; i < reviewers.length; i++)
          Transform.translate(
            offset: Offset(-8.0 * i, 0),
            child: _SimpleUserAvatar(user: reviewers[i]),
          ),
      ],
    );
  }
}

class _SimpleUserAvatar extends StatelessWidget {
  const _SimpleUserAvatar({required this.user});

  final User user;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: _tooltipMessage,
      child: CircleAvatar(
        backgroundColor: _avatarColor,
        radius: 16,
        child: Text(
          user.initials,
          style: Theme.of(context)
              .textTheme
              .labelMedium
              ?.apply(fontWeightDelta: 4),
        ),
      ),
    );
  }

  String get _tooltipMessage {
    String result = user.name;
    if (user.launchpadHandle != null) {
      result = '$result\n${user.launchpadHandle}';
    }
    return result;
  }

  Color get _avatarColor => possibleColors[user.id % possibleColors.length];
}
