import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/filtered_artefact_environments.dart';
import '../../routing.dart';
import '../spacing.dart';

class RerunFilteredEnvironmentsButton extends ConsumerWidget {
  const RerunFilteredEnvironmentsButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final artefactId = AppRoutes.artefactIdFromUri(pageUri);
    final artefactEnvironments =
        ref.watch(filteredArtefactEnvironmentsProvider(pageUri)).value ?? [];

    return TextButton(
      onPressed: () {
        final testExecutions =
            artefactEnvironments.map((ae) => ae.runsDescending.first).toList();
        showDialog(
          context: context,
          builder: (_) => _ConfirmationDialog(
            testExecutions: testExecutions,
            artefactId: artefactId,
          ),
        );
      },
      child: Text(
        'Rerun ${artefactEnvironments.length} Filtered Environments',
        textScaler: const TextScaler.linear(1.2),
      ),
    );
  }
}

class _ConfirmationDialog extends ConsumerWidget {
  const _ConfirmationDialog({
    required this.testExecutions,
    required this.artefactId,
  });

  final List<TestExecution> testExecutions;

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handleYes() {
      final testExecutionIds = {for (final te in testExecutions) te.id};

      ref
          .read(artefactBuildsProvider(artefactId).notifier)
          .rerunTestExecutions(testExecutionIds);

      context.pop();
    }

    return AlertDialog(
      scrollable: true,
      title: Text(
        'Are you sure you want to rerun the following'
        ' ${testExecutions.length} environments?',
      ),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: testExecutions
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
