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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'artefact.dart' hide Artefact;
import 'artefact_versions.dart';

part 'previous_artefact_environment_data.g.dart';

typedef PreviousArtefactEnvironmentData = ({
  String version,
  int environmentCount,
});

/// Returns the version and environment count of the version immediately
/// preceding the given artefact. If the artefact is already the oldest version
/// or if the artefact is absent in the versions list, returns `null`.
@riverpod
Future<PreviousArtefactEnvironmentData?> previousArtefactEnvironmentData(
  Ref ref,
  int artefactId,
) async {
  final versions = await ref.watch(artefactVersionsProvider(artefactId).future);
  // Versions are sorted by artefact ID descending (newest first).
  // Since artefacts are fairly agnostic about what the artefact actually represents,
  // we can't make any assumptions about how the artefact is versioned,
  // so there is no way to sort things other than by artefact ID.
  final sortedVersions = [...versions]
    ..sort((a, b) => b.artefactId.compareTo(a.artefactId));
  final currentIndex =
      sortedVersions.indexWhere((v) => v.artefactId == artefactId);
  if (currentIndex == -1 || currentIndex >= sortedVersions.length - 1) {
    return null;
  }
  final previousVersion = sortedVersions[currentIndex + 1];
  final previousArtefactId = previousVersion.artefactId;
  final previousArtefact =
      await ref.watch(artefactProvider(previousArtefactId).future);
  return (
    version: previousVersion.version,
    environmentCount: previousArtefact.allEnvironmentReviewsCount,
  );
}
