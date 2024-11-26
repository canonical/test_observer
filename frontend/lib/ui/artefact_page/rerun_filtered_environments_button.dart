import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/artefact_environment.dart';
import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../../routing.dart';
import '../spacing.dart';

class RerunFilteredEnvironmentsButton extends StatelessWidget {
  const RerunFilteredEnvironmentsButton({
    super.key,
    required this.filteredArtefactEnvironments,
  });

  final List<ArtefactEnvironment> filteredArtefactEnvironments;

  @override
  Widget build(BuildContext context) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));
    final testExecutionsToRerun =
        filteredArtefactEnvironments.map((ae) => ae.runsDescending.first);

    handlePress() => showDialog(
          context: context,
          builder: (_) => _ConfirmationDialog(
            testExecutionToRerun: testExecutionsToRerun,
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
    required this.testExecutionToRerun,
    required this.artefactId,
  });

  final Iterable<TestExecution> testExecutionToRerun;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handleYes() {
      final testExecutionIds = {for (final te in testExecutionToRerun) te.id};
      ref
          .read(artefactBuildsProvider(artefactId).notifier)
          .rerunTestExecutions(testExecutionIds);
      context.pop();
    }

    return AlertDialog(
      scrollable: true,
      title: Text(
        'Are you sure you want to rerun the following'
        ' ${testExecutionToRerun.length} environments?',
      ),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: testExecutionToRerun
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
