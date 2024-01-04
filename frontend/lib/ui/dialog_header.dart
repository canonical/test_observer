import 'package:flutter/material.dart';
import 'package:yaru_icons/yaru_icons.dart';

import 'spacing.dart';

class DialogHeader extends StatelessWidget {
  const DialogHeader({super.key, this.heading = const SizedBox.shrink()});

  final Widget heading;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: Spacing.level4),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
      ),
      child: Row(
        children: [
          heading,
          const Spacer(),
          InkWell(
            child: const Icon(
              YaruIcons.window_close,
              size: 60,
            ),
            onTap: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }
}
