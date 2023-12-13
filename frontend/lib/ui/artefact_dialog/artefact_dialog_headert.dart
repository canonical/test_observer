import 'package:flutter/material.dart';
import 'package:yaru_icons/yaru_icons.dart';

import '../spacing.dart';

class ArtefactDialogHeader extends StatelessWidget {
  const ArtefactDialogHeader({super.key, required this.title});

  final String title;

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
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineLarge),
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
