import 'package:flutter/material.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/artefact_build.dart';
import '../spacing.dart';
import 'test_execution_expandable.dart';

class ArtefactBuildExpandable extends StatelessWidget {
  const ArtefactBuildExpandable({super.key, required this.artefactBuild});

  final ArtefactBuild artefactBuild;

  @override
  Widget build(BuildContext context) {
    final revisionText =
        artefactBuild.revision == null ? '' : ' (${artefactBuild.revision})';

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
      children: artefactBuild.testExecutions
          .map(
            (testExecution) =>
                TestExecutionExpandable(testExecution: testExecution),
          )
          .toList(),
    );
  }
}
