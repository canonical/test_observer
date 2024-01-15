import 'package:flutter/material.dart';

import '../../models/artefact.dart';
import '../dialog_header.dart';
import '../spacing.dart';
import '../user_avatar.dart';
import 'artefact_signoff_button.dart';

class ArtefactDialogHeader extends StatelessWidget {
  const ArtefactDialogHeader({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final assignee = artefact.assignee;
    return DialogHeader(
      heading: Row(
        children: [
          Text(artefact.name, style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(width: Spacing.level4),
          ArtefactSignoffButton(artefact: artefact),
          const SizedBox(width: Spacing.level4),
          if (assignee != null) UserAvatar(user: assignee),
        ],
      ),
    );
  }
}
