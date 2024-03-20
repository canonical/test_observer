import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/stage_name.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'stage_column.dart';

class DashboardBody extends ConsumerWidget {
  const DashboardBody({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));
    final stages = familyStages(family);

    return ListView.separated(
      padding: const EdgeInsets.only(
        right: Spacing.pageHorizontalPadding,
      ),
      scrollDirection: Axis.horizontal,
      itemBuilder: (_, i) => StageColumn(stage: stages[i]),
      separatorBuilder: (_, __) => const SizedBox(width: Spacing.level5),
      itemCount: stages.length,
    );
  }
}
