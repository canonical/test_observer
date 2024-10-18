import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/test_execution.dart';
import '../../providers/rerun_requests.dart';
import '../spacing.dart';

class RerunFilteredEnvironmentsButton extends ConsumerWidget {
  const RerunFilteredEnvironmentsButton({
    super.key,
    required this.filteredTestExecutions,
  });

  final Iterable<TestExecution> filteredTestExecutions;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handlePress() => showDialog(
          context: context,
          builder: (_) => _ConfirmationDialog(
            filteredTestExecutions: filteredTestExecutions,
          ),
        );

    return TextButton(
      onPressed: handlePress,
      child: Text(
        'Rerun ${filteredTestExecutions.length} Filtered Environments',
        textScaler: const TextScaler.linear(1.2),
      ),
    );
  }
}

class _ConfirmationDialog extends ConsumerWidget {
  const _ConfirmationDialog({required this.filteredTestExecutions});

  final Iterable<TestExecution> filteredTestExecutions;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handleYes() {
      final testExecutionIds = {for (final te in filteredTestExecutions) te.id};
      ref
          .read(rerunRequestsProvider.notifier)
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
