import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';

import 'spacing.dart';

class Header extends StatelessWidget {
  const Header({Key? key, required this.title}) : super(key: key);

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
                children: const [
                  _LegendEntry(
                    icon: Icon(YaruIcons.ok, color: YaruColors.success),
                    text: 'Passed',
                  ),
                  SizedBox(width: Spacing.level4),
                  _LegendEntry(
                    icon: Icon(YaruIcons.error, color: YaruColors.red),
                    text: 'Failed',
                  ),
                  SizedBox(width: Spacing.level4),
                  _LegendEntry(
                    icon: Icon(YaruIcons.information),
                    text: 'No result',
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
