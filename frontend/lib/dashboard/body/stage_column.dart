import 'package:flutter/material.dart';

import '../../spacing.dart';
import 'artefact_card.dart';

class StageColumn extends StatelessWidget {
  const StageColumn({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: ArtefactCard.width,
      child: ListView.separated(
        itemBuilder: (_, __) => const ArtefactCard(),
        separatorBuilder: (_, __) => const SizedBox(height: Spacing.level4),
        itemCount: 2,
      ),
    );
  }
}
