import 'package:flutter/material.dart';

import '../models/user.dart';

Color userIdToColor(int userId) {
  const colorGroups = Colors.accents;
  return colorGroups[userId % colorGroups.length];
}

class UserAvatar extends StatelessWidget {
  const UserAvatar({super.key, required this.user});

  final User user;

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      backgroundColor: userIdToColor(user.id),
      child: Tooltip(
        message:
            '${user.name}\n${user.launchpadEmail}\n${user.launchpadHandle}',
        child: Text(
          user.initials,
          style:
              Theme.of(context).textTheme.labelLarge?.apply(fontWeightDelta: 4),
        ),
      ),
    );
  }
}
