import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/page_filters.dart';
import '../../providers/search_value.dart';
import '../page_search_bar.dart';
import '../side_filters.dart';

class ArtefactSideFilters extends ConsumerWidget {
  const ArtefactSideFilters({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = GoRouterState.of(context).uri;
    final searchQuery = pageUri.queryParameters['q'];
    final filters = ref.watch(pageFiltersProvider(pageUri));

    return SizedBox(
      width: SideFilters.width,
      child: Column(
        children: [
          PageSearchBar(hintText: 'Search by name'),
          const SizedBox(height: SideFilters.spacingBetweenFilters),
          SideFilters(
            filters: filters,
            onOptionChanged: ref
                .read(pageFiltersProvider(pageUri).notifier)
                .handleFilterOptionChange,
            onSubmit: () {
              final searchValue =
                  ref.read(searchValueProvider(searchQuery)).trim();
              final queryParams = {
                if (searchValue.isNotEmpty) 'q': searchValue,
                ...ref.read(pageFiltersProvider(pageUri)).toQueryParams(),
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
