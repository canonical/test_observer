import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../spacing.dart';
import '../user_avatar.dart';
import 'artefact_signoff_button.dart';

class ArtefactPageHeader extends StatelessWidget {
  const ArtefactPageHeader({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final assignee = artefact.assignee;
    final dueDate = artefact.dueDateString;

    return Row(
      children: [
        Text(artefact.name, style: Theme.of(context).textTheme.headlineLarge),
        const SizedBox(width: Spacing.level4),
        ArtefactSignoffButton(artefact: artefact),
        const SizedBox(width: Spacing.level4),
        UserAvatar(
          user: assignee,
          allEnvironmentReviewsCount: artefact.allEnvironmentReviewsCount,
          completedEnvironmentReviewsCount:
              artefact.completedEnvironmentReviewsCount,
        ),
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
    );
  }
}
