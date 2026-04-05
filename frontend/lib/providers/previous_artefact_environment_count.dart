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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'artefact.dart' hide Artefact;
import 'artefact_versions.dart';

part 'previous_artefact_environment_count.g.dart';

/// Returns the [allEnvironmentReviewsCount] of the version immediately preceding
/// the given artefact. If the artefact is already the oldest version or if the
/// artefact is absent in the versions list, returns `null`.
@riverpod
Future<int?> previousArtefactEnvironmentCount(
  Ref ref,
  int artefactId,
) async {
  final versions = await ref.watch(artefactVersionsProvider(artefactId).future);
  // Versions are sorted by artefact ID descending (newest first).
  final currentIndex = versions.indexWhere((v) => v.artefactId == artefactId);
  if (currentIndex == -1 || currentIndex >= versions.length - 1) return null;
  final previousArtefactId = versions[currentIndex + 1].artefactId;
  final previousArtefact =
      await ref.watch(artefactProvider(previousArtefactId).future);
  return previousArtefact.allEnvironmentReviewsCount;
}
