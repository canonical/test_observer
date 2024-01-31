import 'package:flutter/material.dart';

import '../spacing.dart';
import 'search_field.dart';

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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: Spacing.level4),
          const SearchField(),
        ],
      ),
    );
  }
}
