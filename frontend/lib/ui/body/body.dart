import 'package:flutter/material.dart';

import '../../models/stage.dart';
import '../spacing.dart';
import 'stage_column.dart';

class Body extends StatelessWidget {
  const Body({Key? key, required this.stages}) : super(key: key);

  final List<Stage> stages;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      padding:
          const EdgeInsets.symmetric(horizontal: Spacing.pageHorizontalPadding),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}
