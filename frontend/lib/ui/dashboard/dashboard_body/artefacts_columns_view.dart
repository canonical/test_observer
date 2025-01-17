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

import '../../../models/stage_name.dart';
import '../../../routing.dart';
import '../../spacing.dart';
import '../stage_column.dart';

class ArtefactsColumnsView extends ConsumerWidget {
  const ArtefactsColumnsView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));
    final stages = familyStages(family);

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
