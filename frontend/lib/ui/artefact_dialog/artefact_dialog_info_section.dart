import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../models/stage_name.dart';
import '../../models/test_execution.dart';
import '../../routing.dart';
import '../inline_url_text.dart';
import '../spacing.dart';

class ArtefactDialogInfoSection extends StatelessWidget {
  const ArtefactDialogInfoSection({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final bugLink = artefact.bugLink;
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _StagesRow(artefactStage: artefact.stage),
            const SizedBox(height: Spacing.level3),
            ...artefact.details.entries
                .map<Widget>(
                  (detail) => Text(
                    '${detail.key}: ${detail.value}',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                )
                .intersperse(const SizedBox(height: Spacing.level3)),
            const SizedBox(height: Spacing.level3),
            if (bugLink.isNotBlank)
              InlineUrlText(
                leadingText: 'Bug link: ',
                url: bugLink,
                urlText: bugLink,
                fontStyle: Theme.of(context).textTheme.bodyLarge,
              ),
          ],
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: TestExecutionStatus.values
              .map<Widget>(
                (status) => Row(
                  children: [
                    status.icon,
                    const SizedBox(width: Spacing.level2),
                    Text(
                      status.name,
                      style: Theme.of(context)
                          .textTheme
                          .bodyMedium
                          ?.apply(color: YaruColors.warmGrey),
                    ),
                  ],
                ),
              )
              .intersperse(const SizedBox(height: Spacing.level2))
              .toList(),
        ),
      ],
    );
  }
}

class _StagesRow extends ConsumerWidget {
  const _StagesRow({required this.artefactStage});

  final StageName artefactStage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final stages = familyStages(family);

    final stageNamesWidgets = <Widget>[];
    bool passedSelectedStage = false;
    for (final stage in stages) {
      Color fontColor = YaruColors.warmGrey;
      if (passedSelectedStage) {
        fontColor = YaruColors.textGrey;
      } else if (stage == artefactStage) {
        passedSelectedStage = true;
        fontColor = YaruColors.orange;
      }

      stageNamesWidgets.add(
        Text(
          stage.name.capitalize(),
          style: Theme.of(context).textTheme.bodyLarge?.apply(color: fontColor),
        ),
      );
    }

    return Row(
      children: stageNamesWidgets
          .intersperse(
            Text(' > ', style: Theme.of(context).textTheme.bodyLarge),
          )
          .toList(),
    );
  }
}
