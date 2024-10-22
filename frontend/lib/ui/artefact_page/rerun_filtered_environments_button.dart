import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/filtered_artefact_environment_reviews.dart';
import '../../providers/filtered_test_executions.dart';
import '../../routing.dart';
import '../spacing.dart';

class RerunFilteredEnvironmentsButton extends ConsumerWidget {
  const RerunFilteredEnvironmentsButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final artefactId = AppRoutes.artefactIdFromUri(pageUri);
    final filteredTestExecutions =
        ref.watch(filteredTestExecutionsProvider(pageUri)).value ?? [];
    final filteredEnvironmentReviews =
        ref.watch(filteredArtefactEnvironmentReviewsProvider(pageUri)).value ??
            [];

    final groupedTestExecutions = filteredTestExecutions
        .groupBy((te) => (te.artefactBuildId, te.environment.id));
    final latestTestExecutions = groupedTestExecutions.map(
      (key, testExecutionGroup) =>
          MapEntry(key, testExecutionGroup.maxBy((te) => te.id)),
    );
    final testExecutionsToRerun =
        filteredEnvironmentReviews.fold(<TestExecution>[], (currentList, er) {
      final te = latestTestExecutions[(er.artefactBuild.id, er.environment.id)];
      if (te != null) {
        currentList.add(te);
      }
      return currentList;
    });

    handlePress() => showDialog(
          context: context,
          builder: (_) => _ConfirmationDialog(
            filteredTestExecutions: testExecutionsToRerun,
            artefactId: artefactId,
          ),
        );

    return TextButton(
      onPressed: handlePress,
      child: Text(
        'Rerun ${testExecutionsToRerun.length} Filtered Environments',
        textScaler: const TextScaler.linear(1.2),
      ),
    );
  }
}

class _ConfirmationDialog extends ConsumerWidget {
  const _ConfirmationDialog({
    required this.filteredTestExecutions,
    required this.artefactId,
  });

  final Iterable<TestExecution> filteredTestExecutions;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handleYes() {
      final testExecutionIds = {for (final te in filteredTestExecutions) te.id};
      ref
          .read(artefactBuildsProvider(artefactId).notifier)
          .rerunTestExecutions(testExecutionIds);
      context.pop();
    }

    return AlertDialog(
      scrollable: true,
      title: Text(
        'Are you sure you want to rerun the following'
        ' ${filteredTestExecutions.length} environments?',
      ),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: filteredTestExecutions
            .map<Widget>((te) => Text(te.environment.name))
            .intersperse(const SizedBox(height: Spacing.level2))
            .toList(),
      ),
      actions: [
        TextButton(
          onPressed: handleYes,
          child: const Text('yes'),
        ),
        TextButton(
          onPressed: () => context.pop(),
          child: const Text('no'),
        ),
      ],
    );
  }
}
