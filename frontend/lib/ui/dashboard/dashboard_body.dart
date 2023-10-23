import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../models/artefact.dart';
import '../../models/stage_name.dart';
import '../../providers/stage_artefacts.dart';
import '../../routing.dart';
import '../spacing.dart';

class DashboardBody extends StatelessWidget {
  const DashboardBody({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    final stages = familyStages(AppRoutes.familyFromContext(context));
    return ListView.separated(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => _StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}

class _StageColumn extends ConsumerWidget {
  const _StageColumn({Key? key, required this.stage}) : super(key: key);

  final StageName stage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final artefacts = ref.watch(stageArtefactsProvider(family, stage));

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          stage.name.capitalize(),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: Spacing.level4),
        Expanded(
          child: SizedBox(
            width: _ArtefactCard.width,
            child: artefacts.when(
              data: (artefacts) => ListView.separated(
                itemBuilder: (_, i) => _ArtefactCard(artefact: artefacts[i]),
                separatorBuilder: (_, __) =>
                    const SizedBox(height: Spacing.level4),
                itemCount: artefacts.length,
              ),
              loading: () =>
                  const Center(child: YaruCircularProgressIndicator()),
              error: (error, stackTrace) =>
                  Text('Failed to fetch artefacts: $error'),
            ),
          ),
        ),
      ],
    );
  }
}

class _ArtefactCard extends ConsumerWidget {
  const _ArtefactCard({Key? key, required this.artefact}) : super(key: key);

  final Artefact artefact;
  static const double width = 320;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactDetails = [
      'version: ${artefact.version}',
      ...artefact.source.entries.map((entry) => '${entry.key}: ${entry.value}'),
    ];

    return GestureDetector(
      onTap: () => context.go('${AppRoutes.snaps}/${artefact.id}'),
      child: Card(
        margin: const EdgeInsets.all(0),
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Theme.of(context).colorScheme.outline),
          borderRadius: BorderRadius.circular(2.25),
        ),
        child: Container(
          width: width,
          height: 156,
          padding: const EdgeInsets.all(Spacing.level4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                artefact.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: Spacing.level2),
              ...artefactDetails
                  .map<Widget>((detail) => Text(detail))
                  .intersperse(const SizedBox(height: Spacing.level2)),
            ],
          ),
        ),
      ),
    );
  }
}
