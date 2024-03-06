import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_builds.dart';
import '../spacing.dart';
import 'artefact_build_expandable.dart';
import 'test_executions_side_filters.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactBuilds = ref.watch(ArtefactBuildsProvider(artefact.id));

    return artefactBuilds.when(
      data: (artefactBuilds) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          TestExecutionsSideFilters(artefactId: artefact.id),
          const SizedBox(width: Spacing.level5),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: Spacing.level3),
                Text(
                  'Environments',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: artefactBuilds.length,
                    itemBuilder: (_, i) => Padding(
                      // Padding is to avoid scroll bar covering trailing buttons
                      padding: const EdgeInsets.only(right: Spacing.level3),
                      child: ArtefactBuildExpandable(
                        artefactBuild: artefactBuilds[i],
                        artefactId: artefact.id,
                      ),
                    ),
                  ),
                ),
              ],
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
