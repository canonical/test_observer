import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/artefact_filters.dart';
import '../../providers/search_value.dart';
import '../side_filters.dart';
import 'artefact_search_bar.dart';

class ArtefactSideFilters extends ConsumerWidget {
  const ArtefactSideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final filters = ref.watch(artefactFiltersProvider(pageUri));

    return SizedBox(
      width: SideFilters.width,
      child: Column(
        children: [
          const ArtefactSearchBar(),
          const SizedBox(height: SideFilters.spacingBetweenFilters),
          SideFilters(
            filters: filters,
            onOptionChanged: ref
                .read(artefactFiltersProvider(pageUri).notifier)
                .handleFilterOptionChange,
            onSubmit: () {
              final searchValue = ref.read(searchValueProvider).trim();
              final queryParams = {
                if (searchValue.isNotEmpty) 'q': searchValue,
                ...ref.read(artefactFiltersProvider(pageUri)).toQueryParams(),
              };
              context.go(
                pageUri.replace(queryParameters: queryParams).toString(),
              );
            },
          ),
        ],
      ),
    );
  }
}
