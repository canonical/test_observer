import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../providers/filtered_test_executions.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'rerun_filtered_environments_button.dart';
import 'test_execution_expandable.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final filteredTestExecutions =
        ref.watch(filteredTestExecutionsProvider(pageUri));

    return filteredTestExecutions.when(
      data: (testExecutions) => Column(
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
              const Spacer(),
              const RerunFilteredEnvironmentsButton(),
            ],
          ),
          Expanded(
            child: ListView.builder(
              itemCount: testExecutions.length,
              itemBuilder: (_, i) => Padding(
                // Padding is to avoid scroll bar covering trailing buttons
                padding: const EdgeInsets.only(right: Spacing.level3),
                child: TestExecutionExpandable(
                  testExecution: testExecutions[i],
                ),
              ),
            ),
          ),
        ],
      ),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
      error: (error, stackTrace) {
        return Center(child: Text('Error: $error'));
      },
    );
  }
}
