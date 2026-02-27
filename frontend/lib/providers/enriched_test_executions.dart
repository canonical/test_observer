// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/enriched_test_execution.dart';
import 'artefact_builds.dart';
import 'artefact_environment_reviews.dart';

part 'enriched_test_executions.g.dart';

@riverpod
Future<List<EnrichedTestExecution>> enrichedTestExecutions(
  Ref ref,
  int artefactId,
) async {
  final result = <EnrichedTestExecution>[];
  final builds = await ref.watch(artefactBuildsProvider(artefactId).future);
  final reviews =
      await ref.watch(artefactEnvironmentReviewsProvider(artefactId).future);

  final reviewsMap = {
    for (var r in reviews) (r.artefactBuild.id, r.environment.id): r,
  };

  for (var b in builds) {
    for (var te in b.testExecutions) {
      result.add(
        EnrichedTestExecution(
          testExecution: te,
          environmentReview: reviewsMap[(b.id, te.environment.id)]!,
        ),
      );
    }
  }

  return result;
}
