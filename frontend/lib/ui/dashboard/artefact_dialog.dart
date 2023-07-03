import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru_icons/yaru_icons.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../inline_url_text.dart';
import '../spacing.dart';

class ArtefactDialog extends StatelessWidget {
  const ArtefactDialog({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: SizedBox(
        height: min(800, MediaQuery.of(context).size.height * 0.8),
        width: min(1200, MediaQuery.of(context).size.width * 0.8),
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: Spacing.level5,
            vertical: Spacing.level3,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _ArtefactHeader(title: artefact.name),
              const SizedBox(height: Spacing.level4),
              _ArtefactInfoSection(artefact: artefact),
              const SizedBox(height: Spacing.level4),
              Expanded(child: _EnvironmentsSection(artefact: artefact)),
            ],
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
          )
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
    final artefactDetails = [
      'version: ${artefact.version}',
      ...artefact.source.entries.map((entry) => '${entry.key}: ${entry.value}'),
    ];

    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: artefactDetails
              .map<Widget>(
                (detail) =>
                    Text(detail, style: Theme.of(context).textTheme.bodyLarge),
              )
              .toList()
              .intersperse(const SizedBox(height: Spacing.level2))
              .toList(),
        ),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: TestExecutionStatus.values
              .map(
                (status) => Row(
                  children: [
                    status.icon,
                    const SizedBox(width: Spacing.level2),
                    Text(
                      status.name,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              )
              .toList(),
        ),
      ],
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
      loading: () => const YaruCircularProgressIndicator(),
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
                    const SizedBox(width: Spacing.level3),
                    Text(
                      entry.value.toString(),
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                  ],
                ),
              )
              .toList()
              .intersperse(const SizedBox(width: Spacing.level3))
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
    final jenkinsLink = testExecution.jenkinsLink;
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
              if (jenkinsLink != null)
                InlineUrlText(
                  url: jenkinsLink,
                  urlText: 'Jenkins',
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
      child: const SizedBox.shrink(),
    );
  }
}
