import 'package:flutter/material.dart';

import '../../models/artefact_family.dart';
import '../spacing.dart';
import 'stage_column.dart';

class Body extends StatelessWidget {
  const Body({Key? key, required this.family}) : super(key: key);

  final ArtefactFamily family;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding:
          const EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => StageColumn(stage: family.stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: family.stages.length,
    );
  }
}
