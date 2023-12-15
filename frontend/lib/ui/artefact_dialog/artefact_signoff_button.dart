import 'package:flutter/material.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';

class ArtefactSignoffButton extends StatelessWidget {
  const ArtefactSignoffButton({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.titleMedium;

    return YaruPopupMenuButton(
      child: Text(
        artefact.status.name,
        style: fontStyle?.apply(color: artefact.status.color),
      ),
      itemBuilder: (_) => ArtefactStatus.values
          .map(
            (status) => PopupMenuItem(
              value: status,
              child: Text(
                status.name,
                style: fontStyle?.apply(color: status.color),
              ),
            ),
          )
          .toList(),
    );
  }
}
