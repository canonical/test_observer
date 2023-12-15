import 'package:flutter/material.dart';

import '../../models/artefact.dart';

class ArtefactStatusChip extends StatelessWidget {
  const ArtefactStatusChip({super.key, required this.status});

  final ArtefactStatus status;

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    return Chip(
      label: Text(
        status.name,
        style: fontStyle?.apply(color: status.color),
      ),
      shape: const StadiumBorder(),
    );
  }
}
