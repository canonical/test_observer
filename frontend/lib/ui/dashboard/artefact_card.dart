// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../routing.dart';
import '../spacing.dart';
import '../reviewers_avatars.dart';
import '../vanilla/vanilla_chip.dart';

class ArtefactCard extends ConsumerWidget {
  const ArtefactCard({super.key, required this.artefact});

  final Artefact artefact;
  static const double width = 320;
  static const double height = 182;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dueDate = artefact.dueDateString;

    return GestureDetector(
      onTap: () => navigateToArtefactPage(context, artefact.id),
      child: Card(
        margin: const EdgeInsets.all(0),
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Theme.of(context).colorScheme.outline),
          borderRadius: BorderRadius.circular(2.25),
        ),
        child: Container(
          width: width,
          padding: const EdgeInsets.all(Spacing.level4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                artefact.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              Text('version: ${artefact.version}'),
              if (artefact.track.isNotEmpty) Text('track: ${artefact.track}'),
              if (artefact.store.isNotEmpty) Text('store: ${artefact.store}'),
              if (artefact.branch.isNotEmpty)
                Text('branch: ${artefact.branch}'),
              if (artefact.series.isNotEmpty)
                Text('series: ${artefact.series}'),
              if (artefact.repo.isNotEmpty) Text('repo: ${artefact.repo}'),
              if (artefact.source.isNotEmpty)
                Text('source: ${artefact.source}'),
              if (artefact.os.isNotEmpty) Text('os: ${artefact.os}'),
              if (artefact.release.isNotEmpty)
                Text('release: ${artefact.release}'),
              if (artefact.owner.isNotEmpty) Text('owner: ${artefact.owner}'),
              Row(
                children: [
                  VanillaChip(
                    text: artefact.status.name,
                    fontColor: artefact.status.color,
                  ),
                  const Spacer(),
                  if (dueDate != null)
                    VanillaChip(
                      text: 'Due $dueDate',
                      fontColor: YaruColors.red,
                    ),
                  const Spacer(),
                  ReviewersAvatars(
                    reviewers: artefact.reviewers,
                    allEnvironmentReviewsCount:
                        artefact.allEnvironmentReviewsCount,
                    completedEnvironmentReviewsCount:
                        artefact.completedEnvironmentReviewsCount,
                  ),
                ],
              ),
            ].intersperse(const SizedBox(height: Spacing.level2)).toList(),
          ),
        ),
      ),
    );
  }
}
