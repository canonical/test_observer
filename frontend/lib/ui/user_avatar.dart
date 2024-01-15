import 'package:flutter/material.dart';

import '../models/user.dart';

class UserAvatar extends StatelessWidget {
  const UserAvatar({super.key, required this.user});

  final User user;

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      backgroundColor: user.color,
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
