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

import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_environment.dart';
import 'artefact_builds.dart';
import 'artefact_environment_reviews.dart';

part 'artefact_environments.g.dart';

@riverpod
Future<List<ArtefactEnvironment>> artefactEnvironments(
  ArtefactEnvironmentsRef ref,
  int artefactId,
) async {
  final environmentReviews =
      await ref.watch(artefactEnvironmentReviewsProvider(artefactId).future);
  final builds = await ref.watch(artefactBuildsProvider(artefactId).future);
  final testExecutions = builds.map((build) => build.testExecutions).flatten();
  final groupedTestExecutions =
      testExecutions.groupBy((te) => (te.artefactBuildId, te.environment.id));

  final result = environmentReviews.map(
    (environmentReview) {
      final testExecutions = groupedTestExecutions[(
        environmentReview.artefactBuild.id,
        environmentReview.environment.id
      )]!;
      return ArtefactEnvironment(
        runsDescending: testExecutions.sortedByDescending((te) => te.id),
        review: environmentReview,
      );
    },
  ).toList();

  return result.sortedBy((environment) => environment.review.environment.name);
}
