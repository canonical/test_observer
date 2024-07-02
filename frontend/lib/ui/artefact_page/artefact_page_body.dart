import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../providers/artefact_builds.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'artefact_build_expandable.dart';
import 'rerun_filtered_environments_button.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  int _getCompletedTestExecutionCount(List<ArtefactBuild> artefactBuilds) {
    int completedCount = 0;
    for (final artefactBuild in artefactBuilds) {
      for (final testExecution in artefactBuild.testExecutions) {
        if (testExecution.reviewDecision.isNotEmpty) completedCount++;
      }
    }
    return completedCount;
  }

  int _getTotalTestExecutionCount(List<ArtefactBuild> artefactBuilds) {
    int totalCount = 0;
    for (final artefactBuild in artefactBuilds) {
      totalCount += artefactBuild.testExecutions.length;
    }
    return totalCount;
  }

  double _getPercentage(List<ArtefactBuild> artefactBuilds) {
    final completedCount = _getCompletedTestExecutionCount(artefactBuilds);
    final totalCount = _getTotalTestExecutionCount(artefactBuilds);
    return (completedCount / totalCount);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactBuilds = ref.watch(ArtefactBuildsProvider(artefact.id));

    return artefactBuilds.when(
      data: (artefactBuilds) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const PageFiltersView(searchHint: 'Search by environment name'),
          const SizedBox(width: Spacing.level5),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: Spacing.level3),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.center,
                  textBaseline: TextBaseline.alphabetic,
                  children: [
                    Text(
                      'Environments',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    const SizedBox(width: Spacing.level4),
                    SizedBox(
                      width: 25.0, // specify the width
                      height: 25.0, // specify the height
                      child: CircularProgressIndicator(
                        value: _getPercentage(artefactBuilds),
                        semanticsLabel: 'Circular progress indicator',
                      ),
                    ),
                    const Spacer(),
                    const RerunFilteredEnvironmentsButton(),
                  ],
                ),
                // LinearProgressIndicator(
                //   value: _getPercentage(artefactBuilds),
                //   semanticsLabel: 'Linear progress indicator',
                // ),
                Expanded(
                  child: ListView.builder(
                    itemCount: artefactBuilds.length,
                    itemBuilder: (_, i) => Padding(
                      // Padding is to avoid scroll bar covering trailing buttons
                      padding: const EdgeInsets.only(right: Spacing.level3),
                      child: ArtefactBuildExpandable(
                        artefactBuild: artefactBuilds[i],
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
