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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/stage_name.dart';
import '../../../providers/filtered_family_artefacts.dart';
import '../../../routing.dart';
import '../../spacing.dart';
import '../stage_column.dart';

class ArtefactsColumnsView extends ConsumerWidget {
  const ArtefactsColumnsView({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final uri = AppRoutes.uriFromContext(context);
    final family = AppRoutes.familyFromUri(uri);
    final stages = <String>{
      ...familyStages(family),
      ...ref
          .watch(filteredFamilyArtefactsProvider(uri))
          .values
          .map((a) => a.stage),
    }.toList();

    return ListView.separated(
      padding: const EdgeInsets.only(
        right: Spacing.pageHorizontalPadding,
      ),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}
