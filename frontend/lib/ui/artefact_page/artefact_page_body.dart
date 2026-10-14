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
import 'package:flutter/services.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';
import '../../models/artefact.dart';
import '../../models/artefact_environment.dart';
import '../../models/test_execution.dart';
import '../../providers/environments_issues.dart';
import '../../providers/filtered_artefact_environments.dart';
import '../../providers/tests_issues.dart';
import '../../routing.dart';
import '../../utils/csv.dart';
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
        _MissingEnvironmentsWarning(artefact: artefact),
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
              child: CustomScrollView(
                slivers: environments
                    .map(
                      (env) => SliverPadding(
                        // Padding is to avoid scroll bar covering trailing buttons
                        padding: const EdgeInsets.only(right: Spacing.level3),
                        sliver: EnvironmentExpandable(
                          artefactId: artefact.id,
                          artefactEnvironment: env,
                        ),
                      ),
                    )
                    .toList(),
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

class _MissingEnvironmentsWarning extends ConsumerStatefulWidget {
  const _MissingEnvironmentsWarning({required this.artefact});

  final Artefact artefact;

  @override
  ConsumerState<_MissingEnvironmentsWarning> createState() =>
      _MissingEnvironmentsWarningState();
}

class _MissingEnvironmentsWarningState
    extends ConsumerState<_MissingEnvironmentsWarning> {
  bool _isDismissed = false;
  final _missingEnvironmentsScrollController = ScrollController();

  @override
  void dispose() {
    _missingEnvironmentsScrollController.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant _MissingEnvironmentsWarning oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.artefact.id != widget.artefact.id) {
      _isDismissed = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isDismissed) return const SizedBox.shrink();

    final colorScheme = Theme.of(context).colorScheme;
    final missingEnvironments = widget.artefact.missingExpectedEnvironments;
    if (missingEnvironments.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: Spacing.level3),
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: Spacing.level4,
          vertical: Spacing.level2,
        ),
        decoration: BoxDecoration(
          color: colorScheme.secondaryContainer,
          border: Border.all(color: colorScheme.outlineVariant),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: ExpansionTile(
                leading: Icon(
                  Icons.warning_amber_rounded,
                  color: colorScheme.onSecondaryContainer,
                ),
                tilePadding: EdgeInsets.zero,
                childrenPadding: const EdgeInsets.only(
                  left: Spacing.level4,
                  right: Spacing.level2,
                ),
                title: Text(
                  '${missingEnvironments.length} expected '
                  '${missingEnvironments.length == 1 ? 'environment is' : 'environments are'} '
                  'missing from this version',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: colorScheme.onSecondaryContainer,
                      ),
                ),
                children: [
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 200),
                    child: Scrollbar(
                      controller: _missingEnvironmentsScrollController,
                      child: ListView.separated(
                        controller: _missingEnvironmentsScrollController,
                        primary: false,
                        shrinkWrap: true,
                        itemCount: missingEnvironments.length,
                        separatorBuilder: (context, index) => const Divider(
                          height: Spacing.level2,
                        ),
                        itemBuilder: (context, index) {
                          final environment = missingEnvironments[index];
                          return Padding(
                            padding: const EdgeInsets.symmetric(
                              vertical: Spacing.level1,
                            ),
                            child: Text(
                              '${environment.name} (${environment.architecture})',
                              style: Theme.of(context)
                                  .textTheme
                                  .bodyMedium
                                  ?.copyWith(
                                    color: colorScheme.onSecondaryContainer,
                                  ),
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              tooltip: 'Copy as CSV',
              onPressed: () async {
                final csv = missingEnvironments
                    .map(
                      (environment) => '${sanitizeCSV(environment.name)},'
                          '${sanitizeCSV(environment.architecture)}',
                    )
                    .join('\n');
                try {
                  await Clipboard.setData(ClipboardData(text: csv));
                } catch (_) {
                  if (!context.mounted) return;
                  ScaffoldMessenger.of(context)
                    ..hideCurrentSnackBar()
                    ..showSnackBar(
                      const SnackBar(
                        content: Text('Failed to copy missing environments'),
                      ),
                    );
                  return;
                }
                if (!context.mounted) return;
                ScaffoldMessenger.of(context)
                  ..hideCurrentSnackBar()
                  ..showSnackBar(
                    const SnackBar(
                      content: Text('Missing environments copied as CSV'),
                    ),
                  );
              },
              icon: Icon(
                Icons.content_copy,
                color: colorScheme.onSecondaryContainer,
              ),
            ),
            IconButton(
              tooltip: 'Dismiss warning',
              onPressed: () => setState(() => _isDismissed = true),
              icon: Icon(
                Icons.close,
                color: colorScheme.onSecondaryContainer,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
