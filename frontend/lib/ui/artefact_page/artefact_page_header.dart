import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../providers/artefact_builds.dart';
import '../spacing.dart';
import '../user_avatar.dart';
import 'artefact_signoff_button.dart';

class ArtefactPageHeader extends ConsumerWidget {
  const ArtefactPageHeader(
      {Key? key, required this.artefact, required this.artefactBuilds})
      : super(key: key);

  final Artefact artefact;
  final List<ArtefactBuild> artefactBuilds;

  double _computeRatioCompleted(List<ArtefactBuild> artefactBuilds) {
    int totalTestExecutions = 0, completedTestExecution = 0;
    for (final artefactBuild in artefactBuilds) {
      totalTestExecutions += artefactBuild.testExecutions.length;
      for (final testExecution in artefactBuild.testExecutions) {
        if (testExecution.reviewDecision.isNotEmpty) {
          completedTestExecution++;
        }
      }
    }

    return totalTestExecutions == 0
        ? 0
        : completedTestExecution / totalTestExecutions;
  }

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
            ratioCompleted: _computeRatioCompleted(artefactBuilds),
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
