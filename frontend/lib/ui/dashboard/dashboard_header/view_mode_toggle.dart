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
import 'package:yaru/yaru.dart';

import '../../../models/view_modes.dart';
import '../../../providers/view_mode.dart';

class ViewModeToggle extends ConsumerWidget {
  const ViewModeToggle({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final viewMode = ref.watch(viewModeProvider).value;

    if (viewMode == null) return const SizedBox.shrink();

    return ToggleButtons(
      color: YaruColors.orange,
      selectedColor: YaruColors.orange,
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
