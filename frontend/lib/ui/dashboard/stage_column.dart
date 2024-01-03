import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/stage_name.dart';
import '../../providers/stage_artefacts.dart';
import '../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends ConsumerWidget {
  const StageColumn({Key? key, required this.stage}) : super(key: key);

  final StageName stage;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefacts = ref.watch(stageArtefactsProvider(stage));

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
            child: artefacts.when(
              data: (artefacts) => ListView.separated(
                itemBuilder: (_, i) => ArtefactCard(artefact: artefacts[i]),
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
