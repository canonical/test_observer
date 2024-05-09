import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/artefact_build.dart';
import '../../providers/filtered_test_executions.dart';
import '../spacing.dart';
import 'test_execution_expandable.dart';

class ArtefactBuildExpandable extends ConsumerWidget {
  const ArtefactBuildExpandable({super.key, required this.artefactBuild});

  final ArtefactBuild artefactBuild;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;

    final revisionText =
        artefactBuild.revision == null ? '' : ' (${artefactBuild.revision})';

    final filteredTestExecutions =
        ref.watch(filteredTestExecutionsProvider(pageUri)).toSet();
    final artefactBuildTestExecutions = artefactBuild.testExecutions.toSet();
    final relevantTestExecutions =
        filteredTestExecutions.intersection(artefactBuildTestExecutions);

    return ExpansionTile(
      initiallyExpanded: true,
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      title: Row(
        children: [
          Text(
            artefactBuild.architecture + revisionText,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(width: Spacing.level4),
          ...artefactBuild.testExecutionStatusCounts.entries
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
              .intersperse(const SizedBox(width: Spacing.level4)),
        ],
      ),
      children: relevantTestExecutions
          .map((te) => TestExecutionExpandable(testExecution: te))
          .toList(),
    );
  }
}
