import 'package:flutter/material.dart';
import 'package:yaru_icons/yaru_icons.dart';

import '../../models/artefact.dart';
import '../spacing.dart';

class ArtefactDialog extends StatelessWidget {
  const ArtefactDialog({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: FractionallySizedBox(
        heightFactor: 0.8,
        widthFactor: 0.8,
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level5),
          child: Column(
            children: [
              _Header(title: artefact.name),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(title, style: Theme.of(context).textTheme.headlineLarge),
        InkWell(
          child: const Icon(
            YaruIcons.window_close,
            size: 60,
          ),
          onTap: () => Navigator.pop(context),
        )
      ],
    );
  }
}
