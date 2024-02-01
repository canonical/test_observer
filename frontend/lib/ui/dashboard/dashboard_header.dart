import 'package:flutter/material.dart';

import '../spacing.dart';

class DashboardHeader extends StatelessWidget {
  const DashboardHeader({Key? key, required this.title}) : super(key: key);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        top: Spacing.level5,
        bottom: Spacing.level4,
      ),
      child: Text(title, style: Theme.of(context).textTheme.headlineLarge),
    );
  }
}
