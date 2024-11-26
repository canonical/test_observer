import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';
import '../../models/artefact.dart';
import '../../models/artefact_environment.dart';
import '../../models/test_execution.dart';
import '../../providers/environments_issues.dart';
import '../../providers/filtered_artefact_environments.dart';
import '../../providers/tests_issues.dart';
import '../../routing.dart';
import '../non_blocking_provider_preloader.dart';
import '../spacing.dart';
import 'environment_expandable.dart';
import 'rerun_filtered_environments_button.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final environments = ref
        .watch(filteredArtefactEnvironmentsProvider(pageUri))
        .value
        ?.toList();

    if (environments == null) {
      return const Center(child: YaruCircularProgressIndicator());
    }

    return Column(
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
            const SizedBox(width: Spacing.level4),
            _ArtefactEnvironmentsStatusSummary(
              artefactEnvironments: environments,
            ),
            const Spacer(),
            RerunFilteredEnvironmentsButton(
              filteredArtefactEnvironments: environments,
            ),
          ],
        ),
        NonBlockingProviderPreloader(
          provider: environmentsIssuesProvider,
          child: NonBlockingProviderPreloader(
            provider: testsIssuesProvider,
            child: Expanded(
              child: ListView.builder(
                itemCount: environments.length,
                itemBuilder: (_, i) => Padding(
                  // Padding is to avoid scroll bar covering trailing buttons
                  padding: const EdgeInsets.only(right: Spacing.level3),
                  child: EnvironmentExpandable(
                    artefactEnvironment: environments[i],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _ArtefactEnvironmentsStatusSummary extends StatelessWidget {
  const _ArtefactEnvironmentsStatusSummary({
    required this.artefactEnvironments,
  });

  final Iterable<ArtefactEnvironment> artefactEnvironments;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: _latestExecutionStatusCounts(artefactEnvironments)
          .entries
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
          .intersperse(const SizedBox(width: Spacing.level4))
          .toList(),
    );
  }

  Map<TestExecutionStatus, int> _latestExecutionStatusCounts(
    Iterable<ArtefactEnvironment> artefactEnvironments,
  ) {
    final counts = {for (final status in TestExecutionStatus.values) status: 0};

    for (final artefactEnvironment in artefactEnvironments) {
      final status = artefactEnvironment.runsDescending.first.status;
      counts[status] = (counts[status] ?? 0) + 1;
    }

    return counts;
  }
}
