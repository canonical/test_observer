import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import '../models/test_execution.dart';
import 'dio.dart';

part 'artefact_builds.g.dart';

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

  ArtefactBuild _getUpdatedArtefactBuild(
    ArtefactBuild artefactBuild,
    int testExecutionId,
    Map<String, Object?> responseData,
  ) {
    if (artefactBuild.testExecutions.none(
      (element) => element.id == testExecutionId,
    )) {
      return artefactBuild;
    }

    final updatedTestExecutions = artefactBuild.testExecutions.map(
      ((element) {
        if (element.id == testExecutionId) {
          return TestExecution.fromJson(responseData);
        }
        return element;
      }),
    ).toList();

    return artefactBuild.copyWith(testExecutions: updatedTestExecutions);
  }

  Future<void> _updateStateReviewDecision(
    int testExecutionId,
    Map<String, Object?> responseData,
  ) async {
    final previousState = await future;

    state = AsyncData(
      [
        for (final artefactBuild in previousState)
          _getUpdatedArtefactBuild(
            artefactBuild,
            testExecutionId,
            responseData,
          ),
      ],
    );
  }

  Future<void> changeReviewDecision(
    int testExecutionId,
    String reviewComment,
    List<TestExecutionReviewDecision> reviewDecision,
  ) async {
    final dio = ref.watch(dioProvider);

    final response = await dio.patch(
      '/v1/test-executions/$testExecutionId',
      data: TestExecution.updateReviewDecisionRequestData(
        reviewComment,
        reviewDecision,
      ),
    );

    await _updateStateReviewDecision(testExecutionId, response.data);
  }
}
