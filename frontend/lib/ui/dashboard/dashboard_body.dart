import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/stage_name.dart';
import '../../providers/family_artefacts.dart';
import '../../routing.dart';
import '../spacing.dart';
import 'side_filters.dart';
import 'stage_column.dart';

class DashboardBody extends ConsumerStatefulWidget {
  const DashboardBody({Key? key}) : super(key: key);

  @override
  ConsumerState<DashboardBody> createState() => _DashboardBodyState();
}

class _DashboardBodyState extends ConsumerState<DashboardBody> {
  bool showFilters = false;

  @override
  Widget build(BuildContext context) {
    final family = AppRoutes.familyFromContext(context);
    final stages = familyStages(family);

    final artefacts = ref.watch(familyArtefactsProvider(family));

    return artefacts.when(
      data: (_) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          YaruOptionButton(
            child: const Icon(Icons.filter_alt),
            onPressed: () => setState(() {
              showFilters = !showFilters;
            }),
          ),
          if (showFilters) const SideFilters(),
          const SizedBox(width: Spacing.level5),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.only(
                right: Spacing.pageHorizontalPadding,
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
