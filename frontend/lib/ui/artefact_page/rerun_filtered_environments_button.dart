import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/filtered_test_execution_ids.dart';

class RerunFilteredEnvironmentsButton extends ConsumerWidget {
  const RerunFilteredEnvironmentsButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;

    final filteredTestExecutionCount = ref.watch(
      filteredTestExecutionIdsProvider(pageUri).select((ids) => ids.length),
    );

    return TextButton(
      onPressed: () {},
      child: Text(
        'Rerun $filteredTestExecutionCount Filtered Environments',
        textScaler: const TextScaler.linear(1.2),
      ),
    );
  }
}
