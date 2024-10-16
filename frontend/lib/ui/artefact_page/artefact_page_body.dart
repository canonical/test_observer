import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';
import '../../models/artefact.dart';
import '../../models/environment_review.dart';
import '../../models/test_execution.dart';
import '../../providers/environments_issues.dart';
import '../../providers/filtered_artefact_environment_reviews.dart';
import '../../providers/filtered_test_executions.dart';
import '../../providers/tests_issues.dart';
import '../../routing.dart';
import '../non_blocking_provider_preloader.dart';
import '../spacing.dart';
import 'rerun_filtered_environments_button.dart';
import 'test_execution_expandable/test_execution_expandable.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final filteredTestExecutions =
        ref.watch(filteredTestExecutionsProvider(pageUri)).value;
    final filteredEnvironmentReviews =
        ref.watch(filteredArtefactEnvironmentReviewsProvider(pageUri)).value;

    if (filteredTestExecutions == null || filteredEnvironmentReviews == null) {
      return const YaruCircularProgressIndicator();
    }

    final reviewsMap = {
      for (final review in filteredEnvironmentReviews)
        (review.artefactBuild.id, review.environment.id): review,
    };
    final List<(EnvironmentReview, TestExecution)> filteredCombination = [];
    for (final te in filteredTestExecutions) {
      final review = reviewsMap[(te.artefactBuildId, te.environment.id)];
      if (review != null) filteredCombination.add((review, te));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              'Environments',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(width: Spacing.level4),
            _TestExecutionsStatusSummary(
              testExecutions: filteredCombination.map((comb) => comb.$2),
            ),
            const Spacer(),
            const RerunFilteredEnvironmentsButton(),
          ],
        ),
        NonBlockingProviderPreloader(
          provider: environmentsIssuesProvider,
          child: NonBlockingProviderPreloader(
            provider: testsIssuesProvider,
            child: Expanded(
              child: ListView.builder(
                itemCount: filteredCombination.length,
                itemBuilder: (_, i) => Padding(
                  // Padding is to avoid scroll bar covering trailing buttons
                  padding: const EdgeInsets.only(right: Spacing.level3),
                  child: TestExecutionExpandable(
                    testExecution: filteredCombination[i].$2,
                    environmentReview: filteredCombination[i].$1,
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _TestExecutionsStatusSummary extends StatelessWidget {
  const _TestExecutionsStatusSummary({required this.testExecutions});

  final Iterable<TestExecution> testExecutions;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: _testExecutionStatusCounts(testExecutions)
          .entries
          .map<Widget>(
            (entry) => Row(
              children: [
                entry.key.icon,
                const SizedBox(width: Spacing.level2),
                Text(
                  entry.value.toString(),
                  style: Theme.of(context).textTheme.titleLarge,
                ),
              ],
            ),
          )
          .intersperse(const SizedBox(width: Spacing.level4))
          .toList(),
    );
  }

  Map<TestExecutionStatus, int> _testExecutionStatusCounts(
    Iterable<TestExecution> testExecutions,
  ) {
    final counts = {for (final status in TestExecutionStatus.values) status: 0};

    for (final testExecution in testExecutions) {
      final status = testExecution.status;
      counts[status] = (counts[status] ?? 0) + 1;
    }

    return counts;
  }
}
