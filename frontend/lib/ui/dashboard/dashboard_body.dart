import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/stage_name.dart';
import '../../providers/filtered_artefacts.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'side_filters.dart';
import 'stage_column.dart';

class DashboardBody extends ConsumerWidget {
  const DashboardBody({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final stages = familyStages(family);

    final artefacts = ref.watch(filteredArtefactsProvider(family));

    return artefacts.when(
      data: (_) => Row(
        children: [
          const SideFilters(),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(
                horizontal: Spacing.pageHorizontalPadding,
              ),
              scrollDirection: Axis.horizontal,
              itemBuilder: (_, i) => StageColumn(stage: stages[i]),
              separatorBuilder: (_, __) =>
                  const SizedBox(width: Spacing.level5),
              itemCount: stages.length,
            ),
          ),
        ],
      ),
      error: (e, stack) =>
          Center(child: Text('Error:\n$e\nStackTrace:\n$stack')),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
    );
  }
}
