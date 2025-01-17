// Copyright (C) 2024 Canonical Ltd.
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

import '../../../models/view_modes.dart';
import '../../../providers/view_mode.dart';

class ViewModeToggle extends ConsumerWidget {
  const ViewModeToggle({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final viewMode = ref.watch(viewModeProvider).value;

    if (viewMode == null) return const SizedBox.shrink();

    return ToggleButtons(
      isSelected: [
        viewMode == ViewModes.list,
        viewMode == ViewModes.dashboard,
      ],
      children: const [Icon(Icons.list), Icon(Icons.dashboard)],
      onPressed: (i) {
        final selectedView = [ViewModes.list, ViewModes.dashboard][i];
        ref.watch(viewModeProvider.notifier).set(selectedView);
      },
    );
  }
}
