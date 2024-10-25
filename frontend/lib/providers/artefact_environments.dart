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
