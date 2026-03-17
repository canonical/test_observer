// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../models/family_name.dart';
import '../../models/stage_name.dart';
import '../../providers/filtered_family_artefacts.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends ConsumerWidget {
  const StageColumn({super.key, required this.stage});

  final StageName stage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final family = AppRoutes.familyFromUri(pageUri);
    final artefacts = [
      for (final artefact
          in ref.watch(filteredFamilyArtefactsProvider(pageUri)).values)
        if (artefact.stage == stage) artefact,
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          (stage.isEmpty && family == FamilyName.deb)
              ? 'PPAs'
              : stage.name.capitalize(),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: Spacing.level4),
        Expanded(
          child: SizedBox(
            width: ArtefactCard.width,
            child: ListView.separated(
              itemBuilder: (_, i) => ArtefactCard(artefact: artefacts[i]),
              separatorBuilder: (_, __) =>
                  const SizedBox(height: Spacing.level4),
              itemCount: artefacts.length,
            ),
          ),
        ),
      ],
    );
  }
}
