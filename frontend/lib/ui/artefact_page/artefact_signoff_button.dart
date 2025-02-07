// Copyright (C) 2023-2025 Canonical Ltd.
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
import 'package:yaru/widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact.dart' hide Artefact;

class ArtefactSignoffButton extends ConsumerWidget {
  const ArtefactSignoffButton({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final fontStyle = Theme.of(context).textTheme.titleMedium;

    return YaruPopupMenuButton(
      child: Text(
        artefact.status.name,
        style: fontStyle?.apply(color: artefact.status.color),
      ),
      itemBuilder: (_) => ArtefactStatus.values
          .map(
            (status) => PopupMenuItem(
              value: status,
              onTap: () => ref
                  .read(artefactProvider(artefact.id).notifier)
                  .changeArtefactStatus(artefact.id, status),
              child: Text(
                status.name,
                style: fontStyle?.apply(color: status.color),
              ),
            ),
          )
          .toList(),
    );
  }
}
