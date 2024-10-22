import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../models/environment_review.dart';
import '../../providers/filtered_test_executions.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'environment_issues/environment_issues_expandable.dart';
import 'environment_review_button.dart';
import 'test_execution_expandable/test_execution_expandable.dart';

class EnvironmentExpandable extends ConsumerWidget {
  const EnvironmentExpandable({super.key, required this.environmentReview});

  final EnvironmentReview environmentReview;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final testExecutions = ref
        .watch(
          filteredTestExecutionsProvider(pageUri).select(
            (data) => data.whenData(
              (testExecutions) => testExecutions.filter(
                (te) => te.environment.id == environmentReview.environment.id,
              ),
            ),
          ),
        )
        .value;

    if (testExecutions == null) {
      return const Center(child: YaruCircularProgressIndicator());
    }

    if (testExecutions.isEmpty) return const SizedBox.shrink();

    final sortedTestExecutions =
        testExecutions.sortedByDescending((te) => te.id);

    return Expandable(
      title: _EnvironmentExpandableTitle(
        environmentReview: environmentReview,
      ),
      children: [
        EnvironmentIssuesExpandable(environment: environmentReview.environment),
        ...sortedTestExecutions.mapIndexed(
          (i, te) => TestExecutionExpandable(
            testExecution: te,
            runNumber: testExecutions.length - i,
          ),
        ),
      ],
    );
  }
}

class _EnvironmentExpandableTitle extends StatelessWidget {
  const _EnvironmentExpandableTitle({required this.environmentReview});

  final EnvironmentReview environmentReview;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          environmentReview.environment.architecture,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(width: Spacing.level4),
        Text(
          environmentReview.environment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        EnvironmentReviewButton(environmentReview: environmentReview),
      ],
    );
  }
}
