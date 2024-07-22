import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../spacing.dart';
import '../user_avatar.dart';
import 'artefact_signoff_button.dart';

class ArtefactPageHeader extends ConsumerWidget {
  const ArtefactPageHeader(
      {Key? key, required this.artefact, required this.artefactBuilds})
      : super(key: key);

  final Artefact artefact;
  final List<ArtefactBuild> artefactBuilds;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assignee = artefact.assignee;
    final dueDate = artefact.dueDateString;

    return Row(
      children: [
        Text(artefact.name, style: Theme.of(context).textTheme.headlineLarge),
        const SizedBox(width: Spacing.level4),
        ArtefactSignoffButton(artefact: artefact),
        const SizedBox(width: Spacing.level4),
        if (assignee != null)
          UserAvatar(
            user: assignee,
            allTestExecutionsCount: artefact.allTestExecutionsCount,
            completedTestExecutionsCount: artefact.completedTestExecutionsCount,
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
