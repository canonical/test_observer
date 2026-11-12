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
import 'package:yaru/widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact.dart' hide Artefact;

class ArtefactSignoffButton extends ConsumerWidget {
  const ArtefactSignoffButton({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final fontStyle = theme.textTheme.titleMedium;

    return YaruPopupMenuButton(
      child: Text(
        artefact.status.name,
        style: fontStyle?.apply(color: artefact.status.color),
      ),
      itemBuilder: (_) => ArtefactStatus.values.map(
        (status) {
          final enabled = status != ArtefactStatus.approved ||
              artefact.allEnvironmentReviewsCount > 0;
          return PopupMenuItem(
            value: status,
            enabled: enabled,
            onTap: () => ref
                .read(artefactProvider(artefact.id).notifier)
                .changeArtefactStatus(artefact.id, status),
            child: Text(
              status.name,
              style: fontStyle?.apply(
                color: enabled ? status.color : theme.disabledColor,
              ),
            ),
          );
        },
      ).toList(),
    );
  }
}
