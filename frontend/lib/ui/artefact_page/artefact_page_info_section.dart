// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../models/artefact_version.dart';
import '../../models/stage_name.dart';
import '../../providers/artefact.dart' hide Artefact;
import '../../providers/artefact_versions.dart';
import '../../routing.dart';
import '../inline_url_text.dart';
import '../spacing.dart';
import '../submittable_text_field.dart';

class ArtefactPageInfoSection extends ConsumerWidget {
  const ArtefactPageInfoSection({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final bugLink = artefact.bugLink;
    final fontStyle = Theme.of(context).textTheme.bodyLarge;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (!artefact.stage.isEmpty) _StagesRow(artefactStage: artefact.stage),
        _ArtefactVersionSelector(artefact: artefact, labelFontStyle: fontStyle),
        if (artefact.track.isNotEmpty)
          Text('track: ${artefact.track}', style: fontStyle),
        if (artefact.store.isNotEmpty)
          Text('store: ${artefact.store}', style: fontStyle),
        if (artefact.branch.isNotEmpty)
          Text('branch: ${artefact.branch}', style: fontStyle),
        if (artefact.series.isNotEmpty)
          Text('series: ${artefact.series}', style: fontStyle),
        if (artefact.repo.isNotEmpty)
          Text('repo: ${artefact.repo}', style: fontStyle),
        if (artefact.source.isNotEmpty)
          Text('source: ${artefact.source}', style: fontStyle),
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
        SubmittableTextField(
          title: Text('comment: ', style: fontStyle),
          hintText: 'Add a comment',
          initialValue: artefact.comment,
          onSubmit:
              ref.read(artefactProvider(artefact.id).notifier).updateComment,
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
    final currentVersion =
        ArtefactVersion(artefactId: artefact.id, version: artefact.version);
    final versions = ref.watch(artefactVersionsProvider(artefact.id)).value ??
        [currentVersion];

    return Row(
      children: [
        Text('version: ', style: labelFontStyle),
        DropdownMenu<ArtefactVersion>(
          initialSelection: currentVersion,
          dropdownMenuEntries: versions
              .map(
                (version) => DropdownMenuEntry<ArtefactVersion>(
                  value: version,
                  label: version.version,
                ),
              )
              .toList(),
          onSelected: (version) {
            if (version != null) {
              navigateToArtefactPage(context, version.artefactId);
            }
          },
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
      if (stage.isEmpty) continue;

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
