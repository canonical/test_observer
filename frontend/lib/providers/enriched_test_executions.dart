import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/enriched_test_execution.dart';
import 'artefact_builds.dart';
import 'artefact_environment_reviews.dart';

part 'enriched_test_executions.g.dart';

@riverpod
Future<List<EnrichedTestExecution>> enrichedTestExecutions(
  EnrichedTestExecutionsRef ref,
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
