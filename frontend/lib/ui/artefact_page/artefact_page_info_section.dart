import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../models/stage_name.dart';
import '../../providers/artefact_versions.dart';
import '../../routing.dart';
import '../inline_url_text.dart';
import '../spacing.dart';

class ArtefactPageInfoSection extends StatelessWidget {
  const ArtefactPageInfoSection({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final bugLink = artefact.bugLink;
    final fontStyle = Theme.of(context).textTheme.bodyLarge;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _StagesRow(artefactStage: artefact.stage),
        _ArtefactVersionSelector(artefact: artefact, labelFontStyle: fontStyle),
        if (artefact.track.isNotEmpty)
          Text('track: ${artefact.track}', style: fontStyle),
        if (artefact.store.isNotEmpty)
          Text('store: ${artefact.store}', style: fontStyle),
        if (artefact.series.isNotEmpty)
          Text('series: ${artefact.series}', style: fontStyle),
        if (artefact.repo.isNotEmpty)
          Text('repo: ${artefact.repo}', style: fontStyle),
        if (artefact.os.isNotEmpty)
          Text('os: ${artefact.os}', style: fontStyle),
        if (artefact.release.isNotEmpty)
          Text('release: ${artefact.release}', style: fontStyle),
        if (artefact.owner.isNotEmpty)
          Text('owner: ${artefact.owner}', style: fontStyle),
        if (artefact.sha256.isNotEmpty)
          Text('sha256: ${artefact.sha256}', style: fontStyle),
        if (artefact.imageUrl.isNotEmpty)
          InlineUrlText(
            leadingText: 'image link: ',
            url: artefact.imageUrl,
            urlText: artefact.imageUrl,
            fontStyle: fontStyle,
          ),
        if (bugLink.isNotBlank)
          InlineUrlText(
            leadingText: 'bug link: ',
            url: bugLink,
            urlText: bugLink,
            fontStyle: fontStyle,
          ),
      ].intersperse(const SizedBox(height: Spacing.level3)).toList(),
    );
  }
}

class _ArtefactVersionSelector extends ConsumerWidget {
  const _ArtefactVersionSelector({required this.artefact, this.labelFontStyle});

  final Artefact artefact;
  final TextStyle? labelFontStyle;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final versions =
        ref.watch(artefactVersionsProvider(artefact.id)).value ?? [];

    return Row(
      children: [
        Text('version: ', style: labelFontStyle),
        YaruPopupMenuButton(
          child: Text(artefact.version),
          itemBuilder: (_) => versions
              .map(
                (version) => PopupMenuItem(
                  child: Text(version.version),
                  onTap: () =>
                      navigateToArtefactPage(context, version.artefactId),
                ),
              )
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
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));
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
