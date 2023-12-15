import 'package:flutter/material.dart';
import 'package:yaru_icons/yaru_icons.dart';

import '../../models/artefact.dart';
import '../spacing.dart';
import 'artefact_signoff_button.dart';

class ArtefactDialogHeader extends StatelessWidget {
  const ArtefactDialogHeader({super.key, required this.artefact});

  final Artefact artefact;

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
          Text(artefact.name, style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(width: Spacing.level4),
          ArtefactSignoffButton(artefact: artefact),
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
