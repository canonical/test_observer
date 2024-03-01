import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

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
    final dueDate = artefact.dueDateString;
    return DialogHeader(
      heading: Row(
        children: [
          Text('bosch-bt-s6lm-kernel',
              style: Theme.of(context).textTheme.headlineLarge),
          const SizedBox(width: Spacing.level4),
          ArtefactSignoffButton(artefact: artefact),
          const SizedBox(width: Spacing.level4),
          if (assignee != null) UserAvatar(user: assignee),
          const SizedBox(width: Spacing.level4),
          if (dueDate != null)
            Text(
              'Due $dueDate',
              style: Theme.of(context)
                  .textTheme
                  .titleMedium
                  ?.apply(color: YaruColors.red),
            ),
        ],
      ),
    );
  }
}
