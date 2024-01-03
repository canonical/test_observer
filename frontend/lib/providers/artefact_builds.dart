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

  void _updateStateNewTestExecution(
    int testExecutionId,
    Map<String, Object?> responseData,
  ) {
    final List<ArtefactBuild> newStateData = [
      for (final artefactBuild in state.value ?? [])
        ArtefactBuild(
          id: artefactBuild.id,
          architecture: artefactBuild.architecture,
          revision: artefactBuild.revision,
          testExecutions: List.from(
            artefactBuild.testExecutions.map(
              (e) {
                if (e.id == testExecutionId) {
                  return TestExecution.fromJson(responseData);
                }
                return e;
              },
            ),
          ),
        ),
    ];

    state = AsyncData(newStateData);
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

    _updateStateNewTestExecution(testExecutionId, response.data);
  }
}
