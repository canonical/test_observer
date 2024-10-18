import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../models/test_execution.dart';
import '../../../providers/rerun_requests.dart';

class RerunButton extends ConsumerWidget {
  const RerunButton({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final rerunRequests = ref.watch(rerunRequestsProvider).value;
    final isRerunRequested =
        rerunRequests?.any((rr) => rr.testExecutionId == testExecution.id) ==
            true;

    final handlePress = isRerunRequested
        ? null
        : () => showDialog(
              context: context,
              builder: (_) => _RerunConfirmationDialog(
                testExecutionId: testExecution.id,
              ),
            );

    return Tooltip(
      message: isRerunRequested ? 'Already requested' : '',
      child: TextButton(
        onPressed: handlePress,
        child: const Text('rerun'),
      ),
    );
  }
}

class _RerunConfirmationDialog extends ConsumerWidget {
  const _RerunConfirmationDialog({required this.testExecutionId});

  final int testExecutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AlertDialog(
      title: const Text(
        'Are you sure you want to rerun this environment?',
      ),
      actions: [
        TextButton(
          autofocus: true,
          onPressed: () {
            ref
                .read(rerunRequestsProvider.notifier)
                .rerunTestExecutions({testExecutionId});
            context.pop();
          },
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
