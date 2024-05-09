import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../providers/artefact_builds.dart';
import '../../providers/filtered_test_executions.dart';
import '../../routing.dart';
import '../spacing.dart';

class RerunFilteredEnvironmentsButton extends ConsumerWidget {
  const RerunFilteredEnvironmentsButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final artefactId = AppRoutes.artefactIdFromUri(pageUri);

    final filteredTestExecutions = ref
        .watch(
          filteredTestExecutionsProvider(pageUri),
        )
        .toList();

    handlePress() => showDialog(
          context: context,
          builder: (_) => AlertDialog(
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
                onPressed: () {
                  final testExecutionIds = {
                    for (final te in filteredTestExecutions) te.id,
                  };
                  ref
                      .read(artefactBuildsProvider(artefactId).notifier)
                      .rerunTestExecutions(testExecutionIds);
                  context.pop();
                },
                child: const Text('yes'),
              ),
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('no'),
              ),
            ],
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
