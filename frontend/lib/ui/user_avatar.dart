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
    required User? user,
    required this.allEnvironmentReviewsCount,
    required this.completedEnvironmentReviewsCount,
  }) : _user = user;

  final User? _user;
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
          _avatar(context),
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

  Widget _avatar(BuildContext context) {
    return CircleAvatar(
      backgroundColor: _avatarColor,
      child: Text(
        _user?.initials ?? 'N/A',
        style:
            Theme.of(context).textTheme.labelLarge?.apply(fontWeightDelta: 4),
      ),
    );
  }

  String get _tooltipMessage {
    String result = 'Completed: $completedEnvironmentReviewsCount / '
        '$allEnvironmentReviewsCount (${(ratioCompleted * 100).round()}%)';
    if (_user == null) {
      result = 'No reviewer assigned\n$result';
    } else {
      result =
          '${_user.name}\n${_user.launchpadHandle}\n${_user.launchpadEmail}\n$result';
    }
    return result;
  }

  Color get _avatarColor {
    if (_user == null) return Colors.grey;
    return possibleColors[_user.id % possibleColors.length];
  }

  Color get _progressColor {
    final hsl = HSLColor.fromColor(_avatarColor);
    final double lightness = (hsl.lightness - 0.2).clamp(0.0, 1.0);

    return hsl.withLightness(lightness).toColor();
  }
}
