import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_icons/yaru_icons.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_builds.dart';
import '../spacing.dart';

class ArtefactDialog extends StatelessWidget {
  const ArtefactDialog({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: FractionallySizedBox(
        heightFactor: 0.8,
        widthFactor: 0.8,
        child: Padding(
          padding: const EdgeInsets.symmetric(
            horizontal: Spacing.level5,
            vertical: Spacing.level3,
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _Header(title: artefact.name),
              const SizedBox(height: Spacing.level4),
              _Info(artefact: artefact),
              const SizedBox(height: Spacing.level4),
              _Environments(artefact: artefact),
            ],
          ),
        ),
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.title});

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

class _Info extends StatelessWidget {
  const _Info({required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    final artefactDetails = [
      'version: ${artefact.version}',
      ...artefact.source.entries.map((entry) => '${entry.key}: ${entry.value}'),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        ...artefactDetails
            .expand(
              (detail) => [
                Text(detail, style: Theme.of(context).textTheme.bodyLarge),
                const SizedBox(height: Spacing.level2),
              ],
            )
            .toList()
      ],
    );
  }
}

class _Environments extends ConsumerWidget {
  const _Environments({required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactBuilds = ref.watch(artefactBuildsProvider(artefact.id));

    return artefactBuilds.when(
      data: (artefactBuilds) => Column(
        children: [
          Text('Environments', style: Theme.of(context).textTheme.titleLarge),
          ...artefactBuilds.map((build) => Text(build.architecture))
        ],
      ),
      loading: () => const YaruCircularProgressIndicator(),
      error: (error, stackTrace) {
        return Center(child: Text('Error: $error'));
      },
    );
  }
}
