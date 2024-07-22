import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import '../models/family_name.dart';
import '../models/test_execution.dart';
import 'api.dart';
import 'family_artefacts.dart';

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
    FamilyName familyName,
    int artefactId,
  ) async {
    final api = ref.read(apiProvider);
    final testExecution = await api.changeTestExecutionReview(
      testExecutionId,
      reviewDecision,
      reviewComment,
    );

    await _updateTestExecutions({testExecutionId}, (_) => testExecution);

    final artefactBuilds = await future;
    final newCompletedTestExecutionsCount = artefactBuilds
        .map(
          (build) => build.testExecutions
              .where((testExecution) => testExecution.reviewDecision.isNotEmpty)
              .length,
        )
        .fold(0, (a, b) => a + b);

    ref
        .read(familyArtefactsProvider(familyName).notifier)
        .updateCompletedTestExecutionsCount(
          artefactId,
          newCompletedTestExecutionsCount,
        );
  }

  Future<void> rerunTestExecutions(Set<int> testExecutionIds) async {
    final api = ref.read(apiProvider);
    final rerunRequests = await api.rerunTestExecutions(testExecutionIds);

    await _updateTestExecutions(
      rerunRequests.map((rr) => rr.testExecutionId).toSet(),
      (te) => te.copyWith(isRerunRequested: true),
    );
  }

  Future<void> _updateTestExecutions(
    Set<int> testExecutionIds,
    TestExecution Function(TestExecution) update,
  ) async {
    final artefactBuilds = await future;
    final newArtefactBuilds = <ArtefactBuild>[];
    for (final ab in artefactBuilds) {
      final newTestExecutions = [
        for (final te in ab.testExecutions)
          if (testExecutionIds.contains(te.id)) update(te) else te,
      ];

      newArtefactBuilds.add(ab.copyWith(testExecutions: newTestExecutions));
    }

    state = AsyncData(newArtefactBuilds);
  }
}
