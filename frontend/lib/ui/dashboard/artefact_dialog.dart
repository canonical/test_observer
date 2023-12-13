import 'dart:math';

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../models/stage_name.dart';
import '../../models/test_execution.dart';
import '../../models/test_result.dart';
import '../../providers/artefact.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/test_results.dart';
import '../../routing.dart';
import '../inline_url_text.dart';
import '../spacing.dart';

class ArtefactDialog extends ConsumerWidget {
  const ArtefactDialog({super.key, required this.artefactId});

  final String artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefact = ref.watch(artefactProvider(artefactId));

    return SelectionArea(
      child: Dialog(
        child: SizedBox(
          height: min(800, MediaQuery.of(context).size.height * 0.8),
          width: min(1200, MediaQuery.of(context).size.width * 0.8),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: Spacing.level5,
              vertical: Spacing.level3,
            ),
            child: artefact.when(
              data: (artefact) => Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _ArtefactHeader(title: artefact.name),
                  const SizedBox(height: Spacing.level4),
                  _ArtefactInfoSection(artefact: artefact),
                  const SizedBox(height: Spacing.level4),
                  Expanded(child: _EnvironmentsSection(artefact: artefact)),
                ],
              ),
              loading: () =>
                  const Center(child: YaruCircularProgressIndicator()),
              error: (error, stackTrace) =>
                  Text('Failed to fetch artefact $artefactId $error'),
            ),
          ),
        ),
      ),
    );
  }
}

class _ArtefactHeader extends StatelessWidget {
  const _ArtefactHeader({required this.title});

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: Spacing.level4),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineLarge),
          InkWell(
            child: const Icon(
              YaruIcons.window_close,
              size: 60,
            ),
            onTap: () => Navigator.pop(context),
          ),
        ],
      ),
    );
  }
}

class _ArtefactInfoSection extends StatelessWidget {
  const _ArtefactInfoSection({required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _StagesRow(artefactStage: artefact.stage),
            const SizedBox(height: Spacing.level3),
            ...artefact.details.entries
                .map<Widget>(
                  (detail) => Text(
                    '${detail.key}: ${detail.value}',
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                )
                .intersperse(const SizedBox(height: Spacing.level3)),
          ],
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: TestExecutionStatus.values
              .map<Widget>(
                (status) => Row(
                  children: [
                    status.icon,
                    const SizedBox(width: Spacing.level2),
                    Text(
                      status.name,
                      style: Theme.of(context)
                          .textTheme
                          .bodyMedium
                          ?.apply(color: YaruColors.warmGrey),
                    ),
                  ],
                ),
              )
              .intersperse(const SizedBox(height: Spacing.level2))
              .toList(),
        ),
      ],
    );
  }
}

class _StagesRow extends ConsumerWidget {
  const _StagesRow({required this.artefactStage});

  final StageName artefactStage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final stages = familyStages(family);

    final stageNamesWidgets = <Widget>[];
    bool passedSelectedStage = false;
    for (final stage in stages) {
      Color fontColor = YaruColors.warmGrey;
      if (passedSelectedStage) {
        fontColor = YaruColors.textGrey;
      } else if (stage == artefactStage) {
        passedSelectedStage = true;
        fontColor = YaruColors.orange;
      }

      stageNamesWidgets.add(
        Text(
          stage.name.capitalize(),
          style: Theme.of(context).textTheme.bodyLarge?.apply(color: fontColor),
        ),
      );
    }

    return Row(
      children: stageNamesWidgets
          .intersperse(
            Text(' > ', style: Theme.of(context).textTheme.bodyLarge),
          )
          .toList(),
    );
  }
}

class _EnvironmentsSection extends ConsumerWidget {
  const _EnvironmentsSection({required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactBuilds = ref.watch(artefactBuildsProvider(artefact.id));

    return artefactBuilds.when(
      data: (artefactBuilds) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Environments', style: Theme.of(context).textTheme.titleLarge),
          Expanded(
            child: ListView.builder(
              itemCount: artefactBuilds.length,
              itemBuilder: (_, i) =>
                  _ArtefactBuildView(artefactBuild: artefactBuilds[i]),
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

class _ArtefactBuildView extends StatelessWidget {
  const _ArtefactBuildView({required this.artefactBuild});

  final ArtefactBuild artefactBuild;

  @override
  Widget build(BuildContext context) {
    final revisionText =
        artefactBuild.revision == null ? '' : ' (${artefactBuild.revision})';

    return YaruExpandable(
      expandButtonPosition: YaruExpandableButtonPosition.start,
      isExpanded: true,
      header: Row(
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
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level4),
        child: Column(
          children: artefactBuild.testExecutions
              .map(
                (testExecution) =>
                    _TestExecutionView(testExecution: testExecution),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _TestExecutionView extends StatelessWidget {
  const _TestExecutionView({required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return YaruExpandable(
      header: Row(
        children: [
          testExecution.status.icon,
          const SizedBox(width: Spacing.level4),
          Text(
            testExecution.environment.name,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const Spacer(),
          Row(
            children: [
              if (ciLink != null)
                InlineUrlText(
                  url: ciLink,
                  urlText: 'CI',
                ),
              const SizedBox(width: Spacing.level3),
              if (c3Link != null)
                InlineUrlText(
                  url: c3Link,
                  urlText: 'C3',
                ),
            ],
          ),
        ],
      ),
      expandButtonPosition: YaruExpandableButtonPosition.start,
      child: Padding(
        padding: const EdgeInsets.only(left: Spacing.level4),
        child: Column(
          children: TestResultStatus.values
              .map(
                (status) => _TestResultsFilter(
                  status: status,
                  testExecutionId: testExecution.id,
                ),
              )
              .toList(),
        ),
      ),
    );
  }
}

class _TestResultsFilter extends ConsumerWidget {
  const _TestResultsFilter({
    required this.status,
    required this.testExecutionId,
  });

  final TestResultStatus status;
  final int testExecutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final testResults = ref.watch(testResultsProvider(testExecutionId));

    Color? fontColor;
    if (status == TestResultStatus.failed) {
      fontColor = YaruColors.red;
    } else if (status == TestResultStatus.passed) {
      fontColor = YaruColors.light.success;
    }

    final headerStyle =
        Theme.of(context).textTheme.titleMedium?.apply(color: fontColor);

    return testResults.when(
      loading: () => const Center(child: YaruCircularProgressIndicator()),
      error: (error, stackTrace) => Center(child: Text('Error: $error')),
      data: (testResults) {
        final filteredTestResults = testResults
            .filter((testResult) => testResult.status == status)
            .toList();

        return YaruExpandable(
          header: Text(
            '${status.name} ${filteredTestResults.length}',
            style: headerStyle,
          ),
          expandButtonPosition: YaruExpandableButtonPosition.start,
          child: const Column(
            children: [],
          ),
        );
      },
    );
  }
}
