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

import '../../../providers/family_artefacts.dart';
import '../../../providers/filtered_family_artefacts.dart';
import '../../../routing.dart';
import '../../spacing.dart';
import 'view_mode_toggle.dart';

class DashboardHeader extends ConsumerWidget {
  const DashboardHeader({super.key, required this.title});

  final String title;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final family = AppRoutes.familyFromUri(pageUri);
    final totalArtefacts = ref.watch(familyArtefactsProvider(family)).value;
    final filteredCount =
        ref.watch(filteredFamilyArtefactsProvider(pageUri)).length;

    return Padding(
      padding: const EdgeInsets.only(
        top: Spacing.level5,
        bottom: Spacing.level4,
      ),
      child: Row(
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineLarge),
          if (totalArtefacts != null) ...[
            const SizedBox(width: Spacing.level4),
            Text(
              totalArtefacts.length == filteredCount
                  ? '$filteredCount artefacts'
                  : '$filteredCount of ${totalArtefacts.length} artefacts',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurfaceVariant,
                  ),
            ),
          ],
          const Spacer(),
          const ViewModeToggle(),
        ],
      ),
    );
  }
}
