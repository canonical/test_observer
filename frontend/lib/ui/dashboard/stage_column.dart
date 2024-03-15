import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../models/stage_name.dart';
import '../../providers/filtered_family_artefacts.dart';
import '../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends ConsumerWidget {
  const StageColumn({Key? key, required this.stage}) : super(key: key);

  final StageName stage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final artefacts = [
      for (final artefact
          in ref.watch(filteredFamilyArtefactsProvider(pageUri)).values)
        if (artefact.stage == stage) artefact,
    ];

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
            width: ArtefactCard.width,
            child: ListView.separated(
              itemBuilder: (_, i) => ArtefactCard(artefact: artefacts[i]),
              separatorBuilder: (_, __) =>
                  const SizedBox(height: Spacing.level4),
              itemCount: artefacts.length,
            ),
          ),
        ),
      ],
    );
  }
}
