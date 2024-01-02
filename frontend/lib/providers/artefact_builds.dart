import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import '../models/test_execution.dart';
import 'dio.dart';

part 'artefact_builds.g.dart';

// @riverpod
// Future<List<ArtefactBuild>> artefactBuilds(
//   ArtefactBuildsRef ref,
//   int artefactId,
// ) async {
//   final dio = ref.watch(dioProvider);

//   final response = await dio.get('/v1/artefacts/$artefactId/builds');
//   final List artefactBuildsJson = response.data;
//   final artefactBuilds =
//       artefactBuildsJson.map((json) => ArtefactBuild.fromJson(json)).toList();
//   return artefactBuilds;
// }

@riverpod
class ArtefactBuilds extends _$ArtefactBuilds {
  @override
  Future<List<ArtefactBuild>> build(int artefactId) async {
    final dio = ref.watch(dioProvider);

    final response = await dio.get('/v1/artefacts/$artefactId/builds');
    final List artefactBuildsJson = response.data;
    final artefactBuilds =
        artefactBuildsJson.map((json) => ArtefactBuild.fromJson(json)).toList();
    return artefactBuilds;
  }

  Future<void> changeReviewDecision(
    int testExecutionId,
    String reviewComment,
    List<TestExecutionReviewDecision> reviewDecision,
  ) async {
    final dio = ref.watch(dioProvider);

    print(reviewDecision.map((e) => e.toJson()).toList());

    final response = await dio.patch(
      '/v1/test-executions/$testExecutionId',
      data: {
        'review_decision': reviewDecision.map((e) => e.toJson()).toList(),
        'review_comment': reviewComment,
      },
    );

    print(response.statusCode);

    final updatedState = await build(artefactId);
    state = AsyncData(updatedState);
  }
}
