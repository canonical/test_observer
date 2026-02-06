// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

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
import 'bulk_environment_selection_controls.dart';
import 'environment_expandable.dart';
import 'manual_testing_button.dart';
import 'rerun_filtered_plans_button.dart';

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
            AddManualTestingButton(artefactId: artefact.id),
            const SizedBox(width: Spacing.level3),
            const RerunFilteredPlansButton(),
          ],
        ),
        const SizedBox(height: Spacing.level3),
        BulkEnvironmentSelectionControls(
          environments: environments,
          artefactId: artefact.id,
        ),
        const SizedBox(height: Spacing.level2),
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
                    artefactId: artefact.id,
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
    final counts = {
      TestExecutionStatus.notStarted: 0,
      TestExecutionStatus.notTested: 0,
      TestExecutionStatus.inProgress: 0,
      TestExecutionStatus.endedPrematurely: 0,
      TestExecutionStatus.failed: 0,
      TestExecutionStatus.passed: 0,
    };

    for (final artefactEnvironment in artefactEnvironments) {
      final status = artefactEnvironment.runsDescending.first.status;
      counts[status] = (counts[status] ?? 0) + 1;
    }

    return counts;
  }
}
