import 'package:flutter/material.dart';

import '../../models/stage_name.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'stage_column.dart';

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
      itemBuilder: (_, i) => StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}
