import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_notifier.dart';

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
                  .read(artefactNotifierProvider(artefact.id).notifier)
                  .changeStatus(status),
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
