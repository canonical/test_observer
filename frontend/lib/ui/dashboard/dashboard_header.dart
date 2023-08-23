import 'package:flutter/material.dart';

import '../../models/test_execution.dart';
import '../spacing.dart';

class DashboardHeader extends StatelessWidget {
  const DashboardHeader({Key? key, required this.title}) : super(key: key);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level6,
        bottom: Spacing.level4,
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(height: Spacing.level4),
              Row(
                children: [
                  _LegendEntry(
                    icon: TestExecutionStatus.failed.icon,
                    text: 'Failed',
                  ),
                  const SizedBox(width: Spacing.level4),
                  _LegendEntry(
                    icon: TestExecutionStatus.notTested.icon,
                    text: 'No result',
                  ),
                  const SizedBox(width: Spacing.level4),
                  _LegendEntry(
                    icon: TestExecutionStatus.passed.icon,
                    text: 'Passed',
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _LegendEntry extends StatelessWidget {
  const _LegendEntry({required this.icon, required this.text});

  final Icon icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        icon,
        const SizedBox(width: Spacing.level3),
        Text(text, style: Theme.of(context).textTheme.labelLarge),
      ],
    );
  }
}
