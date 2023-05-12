import 'package:flutter/material.dart';

import '../../models/stage.dart';
import '../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends StatelessWidget {
  const StageColumn({Key? key, required this.stage}) : super(key: key);

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
            width: ArtefactCard.width,
            child: ListView.separated(
              itemBuilder: (_, i) => ArtefactCard(artefact: stage.artefacts[i]),
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
