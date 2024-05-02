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

    await _updateTestExecution(testExecutionId, (_) => testExecution);
  }

  Future<void> rerunTestExecution(int testExecutionId) async {
    final api = ref.read(apiProvider);
    await api.rerunTestExecution(testExecutionId);

    await _updateTestExecution(
      testExecutionId,
      (te) => te.copyWith(isRerunRequested: true),
    );
  }

  Future<void> _updateTestExecution(
    int testExecutionId,
    TestExecution Function(TestExecution) update,
  ) async {
    final artefactBuilds = await future;
    final newArtefactBuilds = <ArtefactBuild>[];
    for (final ab in artefactBuilds) {
      final newTestExecutions = [
        for (final te in ab.testExecutions)
          if (te.id == testExecutionId) update(te) else te,
      ];

      newArtefactBuilds.add(ab.copyWith(testExecutions: newTestExecutions));
    }

    state = AsyncData(newArtefactBuilds);
  }
}
