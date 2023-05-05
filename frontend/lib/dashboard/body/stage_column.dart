import 'package:flutter/material.dart';

import '../../models/stage.dart';
import '../../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends StatelessWidget {
  const StageColumn({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    const stage = dummyStage;

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
              itemBuilder: (_, __) => const ArtefactCard(),
              separatorBuilder: (_, __) =>
                  const SizedBox(height: Spacing.level4),
              itemCount: 10,
            ),
          ),
        ),
      ],
    );
  }
}
