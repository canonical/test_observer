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

import 'package:dartx/dartx.dart';
import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/user.dart';
import '../repositories/api_repository.dart';
import 'api.dart';

part 'image_respin.g.dart';

// cdimage submits every image it publishes as an execution of this test plan
// in this environment, and its rebuild-requests cron job only picks up rerun
// requests made against those executions.
const imageBuildTestPlan = 'Image build';
const cdimageEnvironment = 'cdimage.ubuntu.com';

class ImageRespinTarget {
  const ImageRespinTarget({
    required this.artefact,
    required this.architecture,
    required this.artefactBuildId,
    required this.testExecutionId,
    required this.isRerunRequested,
  });

  final Artefact artefact;
  final String architecture;
  final int artefactBuildId;
  final int testExecutionId;
  final bool isRerunRequested;
}

class ImageRespinTargets {
  const ImageRespinTargets({required this.targets, required this.skipped});

  final List<ImageRespinTarget> targets;

  /// Images of the release without a cdimage build execution, which cdimage
  /// would never pick a rerun request up for.
  final List<Artefact> skipped;
}

@riverpod
Future<ImageRespinTargets> imageRespinTargets(Ref ref, String release) async {
  if (release.isEmpty) {
    return const ImageRespinTargets(targets: [], skipped: []);
  }

  // Query the API directly rather than through the cached artefact providers,
  // so that invalidating this provider re-reads the rerun state.
  final api = ref.watch(apiProvider);
  final artefacts = (await api.getFamilyArtefacts(FamilyName.image))
      .values
      .where((artefact) => artefact.release == release)
      .sortedBy((artefact) => artefact.name)
      .thenBy((artefact) => artefact.os)
      .toList();
  final artefactsBuilds = await Future.wait(
    artefacts.map((artefact) => api.getArtefactBuilds(artefact.id)),
  );

  final targets = <ImageRespinTarget>[];
  final skipped = <Artefact>[];
  for (final (index, artefact) in artefacts.indexed) {
    final artefactTargets = [
      for (final build in artefactsBuilds[index])
        if (build.testExecutions
                .where(
                  (te) =>
                      te.testPlan == imageBuildTestPlan &&
                      te.environment.name == cdimageEnvironment,
                )
                .maxBy((te) => te.id)
            case final execution?)
          ImageRespinTarget(
            artefact: artefact,
            architecture: build.architecture,
            artefactBuildId: build.id,
            testExecutionId: execution.id,
            isRerunRequested: execution.isRerunRequested,
          ),
    ];

    if (artefactTargets.isEmpty) {
      skipped.add(artefact);
    } else {
      targets.addAll(artefactTargets);
    }
  }

  return ImageRespinTargets(targets: targets, skipped: skipped);
}

sealed class ImageRespinOutcome {
  const ImageRespinOutcome();
}

/// Test Observer confirmed queuing a rerun for every build in
/// [queuedBuildIds]. It found no execution for the builds in
/// [notFoundBuildIds], so nothing was queued for those.
class ImageRespinQueued extends ImageRespinOutcome {
  const ImageRespinQueued({
    required this.queuedBuildIds,
    required this.notFoundBuildIds,
  });

  final Set<int> queuedBuildIds;
  final Set<int> notFoundBuildIds;
}

class ImageRespinNotSignedIn extends ImageRespinOutcome {
  const ImageRespinNotSignedIn();
}

class ImageRespinForbidden extends ImageRespinOutcome {
  const ImageRespinForbidden({required this.userName});

  final String userName;
}

class ImageRespinFailed extends ImageRespinOutcome {
  const ImageRespinFailed({required this.detail});

  final String detail;
}

Future<ImageRespinOutcome> requestImageRespins({
  required ApiRepository api,
  required List<ImageRespinTarget> targets,
  required Future<User?> Function() reloadCurrentUser,
}) async {
  final buildIds = {for (final target in targets) target.artefactBuildId};

  try {
    final queuedBuildIds = await api.requestReruns(
      [for (final target in targets) target.testExecutionId],
    );
    return ImageRespinQueued(
      queuedBuildIds: queuedBuildIds.intersection(buildIds),
      notFoundBuildIds: buildIds.difference(queuedBuildIds),
    );
  } on DioException catch (e) {
    final statusCode = e.response?.statusCode;
    if (statusCode == 401 || statusCode == 403) {
      // The API answers 403 both to missing permissions and to a session
      // that expired since the page loaded, so check which one it is.
      final User? user;
      try {
        user = await reloadCurrentUser();
      } catch (_) {
        return ImageRespinFailed(detail: _errorDetail(e));
      }
      if (user == null) return const ImageRespinNotSignedIn();
      return ImageRespinForbidden(userName: user.name);
    }
    return ImageRespinFailed(detail: _errorDetail(e));
  }
}

String _errorDetail(DioException e) {
  final data = e.response?.data;
  if (data is Map && data['detail'] != null) return data['detail'].toString();
  final statusCode = e.response?.statusCode;
  if (statusCode != null) return 'HTTP $statusCode';
  return e.message ?? 'could not reach Test Observer';
}
