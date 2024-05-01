import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import '../models/test_execution.dart';
import 'api.dart';

part 'artefact_builds.g.dart';

@riverpod
class ArtefactBuilds extends _$ArtefactBuilds {
  @override
  Future<List<ArtefactBuild>> build(int artefactId) async {
    final api = ref.watch(apiProvider);
    return await api.getArtefactBuilds(artefactId);
  }

  ArtefactBuild _getUpdatedArtefactBuild(
    ArtefactBuild artefactBuild,
    int testExecutionId,
    TestExecution updatedTestExecution,
  ) {
    if (artefactBuild.testExecutions.none(
      (element) => element.id == testExecutionId,
    )) {
      return artefactBuild;
    }

    final updatedTestExecutions = artefactBuild.testExecutions.map(
      ((element) {
        if (element.id == testExecutionId) {
          return updatedTestExecution;
        }
        return element;
      }),
    ).toList();

    return artefactBuild.copyWith(testExecutions: updatedTestExecutions);
  }

  Future<void> _updateStateReviewDecision(
    int testExecutionId,
    TestExecution updatedTestExecution,
  ) async {
    final previousState = await future;

    state = AsyncData(
      [
        for (final artefactBuild in previousState)
          _getUpdatedArtefactBuild(
            artefactBuild,
            testExecutionId,
            updatedTestExecution,
          ),
      ],
    );
  }

  Future<void> changeReviewDecision(
    int testExecutionId,
    String reviewComment,
    List<TestExecutionReviewDecision> reviewDecision,
  ) async {
    final api = ref.read(apiProvider);
    final testExecution = await api.changeTestExecutionReview(
      testExecutionId,
      reviewDecision,
      reviewComment,
    );

    await _updateStateReviewDecision(testExecutionId, testExecution);
  }

  Future<void> rerunTestExecution(int testExecutionId) async {
    final api = ref.read(apiProvider);
    await api.rerunTestExecution(testExecutionId);

    final artefactBuilds = await future;
    final newArtefactBuilds = <ArtefactBuild>[];
    for (final ab in artefactBuilds) {
      final newTestExecutions = [
        for (final te in ab.testExecutions)
          if (te.id == testExecutionId)
            te.copyWith(isRerunRequested: true)
          else
            te,
      ];

      newArtefactBuilds.add(ab.copyWith(testExecutions: newTestExecutions));
    }

    state = AsyncData(newArtefactBuilds);
  }
}
