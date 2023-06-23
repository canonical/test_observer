import 'package:flutter/material.dart';

import '../../models/artefact.dart';
import '../../models/stage.dart';
import '../spacing.dart';
import 'artefact_dialog.dart';

class DashboardBody extends StatelessWidget {
  const DashboardBody({Key? key, required this.stages}) : super(key: key);

  final List<Stage> stages;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding:
          const EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => _StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}

class _StageColumn extends StatelessWidget {
  const _StageColumn({Key? key, required this.stage}) : super(key: key);

  final Stage stage;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          stage.name,
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: Spacing.level4),
        Expanded(
          child: SizedBox(
            width: _ArtefactCard.width,
            child: ListView.separated(
              itemBuilder: (_, i) =>
                  _ArtefactCard(artefact: stage.artefacts[i]),
              separatorBuilder: (_, __) =>
                  const SizedBox(height: Spacing.level4),
              itemCount: stage.artefacts.length,
            ),
          ),
        ),
      ],
    );
  }
}

class _ArtefactCard extends StatelessWidget {
  const _ArtefactCard({Key? key, required this.artefact}) : super(key: key);

  final Artefact artefact;
  static const double width = 320;

  @override
  Widget build(BuildContext context) {
    final artefactDetails = [
      'version: ${artefact.version}',
      ...artefact.source.entries.map((entry) => '${entry.key}: ${entry.value}'),
    ];

    return GestureDetector(
      onTap: () => showDialog(
        context: context,
        builder: (_) => ArtefactDialog(
          artefact: artefact,
        ),
      ),
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
                  .expand(
                    (detail) => [
                      Text(detail),
                      const SizedBox(height: Spacing.level2),
                    ],
                  )
                  .toList()
            ],
          ),
        ),
      ),
    );
  }
}
