import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact.dart' hide Artefact;

class ArtefactSignoffButton extends ConsumerWidget {
  const ArtefactSignoffButton({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
              onTap: () => ref
                  .read(artefactProvider(artefact.id).notifier)
                  .changeArtefactStatus(artefact.id, status),
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
