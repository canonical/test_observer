// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/artefact_builds.dart';
import '../../providers/current_user.dart';
import 'manual_testing_dialog.dart';

class AddManualTestingButton extends ConsumerWidget {
  const AddManualTestingButton({
    super.key,
    required this.artefactId,
  });

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).value;
    final artefactBuildsAsync = ref.watch(artefactBuildsProvider(artefactId));

    // Only show the button if the user is logged in
    if (user == null) {
      return const SizedBox.shrink();
    }

    // Only show if builds are loaded and there's at least one build
    return artefactBuildsAsync.when(
      data: (builds) {
        if (builds.isEmpty) {
          return const SizedBox.shrink();
        }

        return TextButton(
          onPressed: () => showDialog(
            context: context,
            builder: (_) => StartManualTestingDialog(
              artefactId: artefactId,
            ),
          ),
          child: Text(
            'Add Manual Testing',
            textScaler: const TextScaler.linear(1.2),
          ),
        );
      },
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
    );
  }
}
