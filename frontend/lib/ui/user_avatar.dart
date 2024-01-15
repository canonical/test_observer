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

Color userIdToColor(int userId) {
  return possibleColors[userId % possibleColors.length];
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
            '${user.name}\n${user.launchpadHandle}\n${user.launchpadEmail}',
        child: Text(
          user.initials,
          style:
              Theme.of(context).textTheme.labelLarge?.apply(fontWeightDelta: 4),
        ),
      ),
    );
  }
}
