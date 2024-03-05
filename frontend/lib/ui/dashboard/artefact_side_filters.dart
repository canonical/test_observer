import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/artefact_filters.dart';
import '../../routing.dart';
import '../side_filters.dart';
import 'artefact_search_bar.dart';

class ArtefactSideFilters extends ConsumerWidget {
  const ArtefactSideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);
    final filters = ref.watch(artefactFiltersProvider(family));

    return SizedBox(
      width: SideFilters.width,
      child: Column(
        children: [
          ArtefactSearchBar(),
          const SizedBox(height: SideFilters.spacingBetweenFilters),
          SideFilters(
            filters: filters,
            onOptionChanged: (filterName, optionName, value) => ref
                .read(artefactFiltersProvider(family).notifier)
                .handleFilterOptionChange(
                  filterName,
                  optionName,
                  value,
                ),
          ),
        ],
      ),
    );
  }
}
