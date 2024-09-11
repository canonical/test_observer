import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_execution.dart';
import 'artefact.dart';
import 'artefact_builds.dart';

part 'review_test_execution.g.dart';

@riverpod
class ReviewTestExecution extends _$ReviewTestExecution {
  @override
  Future<void> build() async {
    return;
  }

  Future<void> reviewTestExecution(
    int testExecutionId,
    String reviewComment,
    List<TestExecutionReviewDecision> reviewDecision,
    int artefactId,
  ) async {
    await ref
        .read(artefactBuildsProvider(artefactId).notifier)
        .changeReviewDecision(
          testExecutionId,
          reviewComment,
          reviewDecision,
        );

    final artefactBuilds =
        ref.read(artefactBuildsProvider(artefactId)).requireValue;

    final newCompletedTestExecutionsCount = artefactBuilds
        .map(
          (build) => build.testExecutions
              .where((testExecution) => testExecution.reviewDecision.isNotEmpty)
              .length,
        )
        .fold(0, (a, b) => a + b);

    await ref
        .read(artefactProvider(artefactId).notifier)
        .updateCompletedTestExecutionsCount(newCompletedTestExecutionsCount);
  }
}
