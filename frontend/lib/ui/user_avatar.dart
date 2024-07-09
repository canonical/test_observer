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

Color getDarkerColor(Color color, [double amount = 0.2]) {
  final hsl = HSLColor.fromColor(color);
  final double lightness = (hsl.lightness - amount).clamp(0.0, 1.0);

  return hsl.withLightness(lightness).toColor();
}

class UserAvatar extends StatelessWidget {
  const UserAvatar(
      {super.key,
      required this.user,
      required this.allTestExecutionsCount,
      required this.completedTestExecutionsCount});

  final User user;
  final int allTestExecutionsCount;
  final int completedTestExecutionsCount;

  double get ratioCompleted {
    if (allTestExecutionsCount == 0) {
      return 0.0;
    }
    return completedTestExecutionsCount / allTestExecutionsCount;
  }

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message:
          '${user.name}\n${user.launchpadHandle}\n${user.launchpadEmail}\nCompleted: $completedTestExecutionsCount / $allTestExecutionsCount (${(ratioCompleted * 100).round()}%)',
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircleAvatar(
            backgroundColor: userIdToColor(user.id),
            child: Text(
              user.initials,
              style: Theme.of(context)
                  .textTheme
                  .labelLarge
                  ?.apply(fontWeightDelta: 4),
            ),
          ),
          SizedBox(
            width: 43.0, // specify the width
            height: 43.0, // specify the height
            child: CircularProgressIndicator(
              color: getDarkerColor(userIdToColor(user.id)),
              backgroundColor: userIdToColor(user.id),
              value: ratioCompleted,
              semanticsLabel: 'Circular progress indicator',
            ),
          ),
        ],
      ),
    );
  }
}
