import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/widgets.dart';

import '../../models/filter.dart';
import '../../providers/page_filter_groups.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import '../expandable.dart';
import 'page_search_bar.dart';
import '../spacing.dart';

class PageFiltersView extends ConsumerWidget {
  const PageFiltersView({super.key, this.searchHint, this.width = 300.0});

  final String? searchHint;
  final double width;

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final searchQuery =
        pageUri.queryParameters[CommonQueryParameters.searchQuery];
    final filterGroups = ref.watch(pageFilterGroupsProvider(pageUri));
    final allFilters =
        filterGroups.map((group) => group.filters).flatten().toList();

    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemBuilder: (_, i) {
          if (i == 0) {
            return PageSearchBar(
              hintText: searchHint,
              onSubmitted: (_) =>
                  submitFilters(ref, searchQuery, pageUri, context),
            );
          }

          if (i == allFilters.length + 1) {
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () =>
                    submitFilters(ref, searchQuery, pageUri, context),
                child: const Text('Apply'),
              ),
            );
          }

          int filterGroupIndex = 0;
          int filtersCounted = filterGroups[filterGroupIndex].filters.length;
          while (i > filtersCounted) {
            filterGroupIndex++;
            filtersCounted += filterGroups[filterGroupIndex].filters.length;
          }

          return _SideFilter(
            filter: allFilters[i - 1],
            onOptionChanged: (
              filterName,
              optionName,
              optionValue,
            ) =>
                ref
                    .read(pageFilterGroupsProvider(pageUri).notifier)
                    .handleFilterOptionChange(
                      filterGroupIndex,
                      filterName,
                      optionName,
                      optionValue,
                    ),
          );
        },
        separatorBuilder: (_, __) =>
            const SizedBox(height: spacingBetweenFilters),
        itemCount: allFilters.length + 2,
      ),
    );
  }

  void submitFilters(
    WidgetRef ref,
    String? searchQuery,
    Uri pageUri,
    BuildContext context,
  ) {
    final sortBy = pageUri.queryParameters[CommonQueryParameters.sortBy];
    final sortDirection =
        pageUri.queryParameters[CommonQueryParameters.sortDirection];
    final searchValue = ref.read(searchValueProvider(searchQuery)).trim();
    final filtersQueryParameters = {
      for (final filterGroup in ref.read(pageFilterGroupsProvider(pageUri)))
        ...filterGroup.toQueryParams(),
    };
    final queryParams = {
      if (searchValue.isNotEmpty)
        CommonQueryParameters.searchQuery: searchValue,
      ...filtersQueryParameters,
      if (sortBy != null) CommonQueryParameters.sortBy: sortBy,
      if (sortDirection != null)
        CommonQueryParameters.sortDirection: sortDirection,
    };
    context.go(
      pageUri.replace(queryParameters: queryParams).toString(),
    );
  }
}

class _SideFilter extends StatelessWidget {
  const _SideFilter({required this.filter, required this.onOptionChanged});

  final Filter filter;
  final Function(String, String, bool) onOptionChanged;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      initiallyExpanded: true,
      title: Text(
        filter.name,
        style: Theme.of(context).textTheme.headlineSmall,
      ),
      children: [
        for (final option in filter.detectedOptions)
          Row(
            children: [
              YaruCheckbox(
                value: filter.selectedOptions.contains(option),
                onChanged: (newValue) {
                  if (newValue != null) {
                    onOptionChanged(filter.name, option, newValue);
                  }
                },
              ),
              Text(option),
            ],
          ),
      ],
    );
  }
}
