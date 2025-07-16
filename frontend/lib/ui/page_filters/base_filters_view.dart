// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/page_filters.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import 'checkbox_list_expandable.dart';
import 'multi_select_combobox.dart';
import 'page_search_bar.dart';
import '../spacing.dart';

/// Base widget that contains the shared logic for rendering filters
class BaseFiltersView extends ConsumerWidget {
  const BaseFiltersView({
    super.key,
    required this.pageUri,
    required this.filters,
    required this.width,
    required this.showSearchBar,
    required this.comboboxFilterNames,
    this.searchHint,
    this.environmentComboboxKey,
  });

  final Uri pageUri;
  final List<FilterState> filters;
  final double width;
  final bool showSearchBar;
  final Set<String> comboboxFilterNames;
  final String? searchHint;
  final GlobalKey<MultiSelectComboboxState>? environmentComboboxKey;

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchQuery =
        pageUri.queryParameters[CommonQueryParameters.searchQuery];

    void submitFilters() {
      final sortBy = pageUri.queryParameters[CommonQueryParameters.sortBy];
      final sortDirection =
          pageUri.queryParameters[CommonQueryParameters.sortDirection];
      final searchValue = ref.read(searchValueProvider(searchQuery)).trim();
      final queryParams = {
        if (searchValue.isNotEmpty)
          CommonQueryParameters.searchQuery: searchValue,
        ...ref.read(pageFiltersProvider(pageUri).notifier).toQueryParams(),
        if (sortBy != null) CommonQueryParameters.sortBy: sortBy,
        if (sortDirection != null)
          CommonQueryParameters.sortDirection: sortDirection,
      };
      context.go(pageUri.replace(queryParameters: queryParams).toString());
    }

    final widgets = <Widget>[];

    // Add search bar if requested
    if (showSearchBar) {
      widgets.add(
        PageSearchBar(
          hintText: searchHint,
          onSubmitted: (_) => submitFilters(),
        ),
      );
    }

    // Process filters in a specific order for comboboxes
    final comboboxFilters = <FilterState>[];
    final regularFilters = <FilterState>[];

    // Separate combobox filters and regular filters
    for (final filter in filters) {
      if (comboboxFilterNames.contains(filter.name)) {
        comboboxFilters.add(filter);
      } else {
        regularFilters.add(filter);
      }
    }

    // Sort combobox filters to ensure Environment comes first
    const filterOrder = ['Environment', 'Test plan'];
    comboboxFilters.sort((a, b) {
      final aIndex = filterOrder.indexOf(a.name);
      final bIndex = filterOrder.indexOf(b.name);

      // If both are in the order list, sort by their position
      if (aIndex != -1 && bIndex != -1) {
        return aIndex.compareTo(bIndex);
      }
      // If only a is in the list, it comes first
      if (aIndex != -1) return -1;
      // If only b is in the list, it comes first
      if (bIndex != -1) return 1;
      // If neither is in the list, sort alphabetically
      return a.name.compareTo(b.name);
    });

    // Add combobox filters first
    for (final filter in comboboxFilters) {
      final options = filter.options.map((e) => e.name).toList();
      final key = filter.name == 'Environment' ? environmentComboboxKey : null;

      // Get initially selected values from filter state
      final initialSelected = filter.options
          .where((option) => option.isSelected)
          .map((option) => option.name)
          .toSet();

      widgets.add(
        MultiSelectCombobox(
          key: key,
          title: filter.name,
          allOptions: options,
          initialSelected: initialSelected,
          maxSuggestions: 10,
          onChanged: (option, isSelected) {
            // Update the filter state
            ref
                .read(pageFiltersProvider(pageUri).notifier)
                .onChanged(filter.name, option, isSelected);

            // Immediately update the URL with new filter state
            final sortBy =
                pageUri.queryParameters[CommonQueryParameters.sortBy];
            final sortDirection =
                pageUri.queryParameters[CommonQueryParameters.sortDirection];
            final searchQuery =
                pageUri.queryParameters[CommonQueryParameters.searchQuery];
            final searchValue =
                ref.read(searchValueProvider(searchQuery)).trim();

            final queryParams = {
              if (searchValue.isNotEmpty)
                CommonQueryParameters.searchQuery: searchValue,
              ...ref
                  .read(pageFiltersProvider(pageUri).notifier)
                  .toQueryParams(),
              if (sortBy != null) CommonQueryParameters.sortBy: sortBy,
              if (sortDirection != null)
                CommonQueryParameters.sortDirection: sortDirection,
            };

            // Navigate to new URL immediately
            context
                .go(pageUri.replace(queryParameters: queryParams).toString());
          },
        ),
      );
    }

    // Add regular filters
    for (final filter in regularFilters) {
      widgets.add(
        CheckboxListExpandable(
          title: filter.name,
          options: filter.options,
          onChanged: (option, isSelected) => ref
              .read(pageFiltersProvider(pageUri).notifier)
              .onChanged(filter.name, option, isSelected),
        ),
      );
    }

    // Add apply button
    widgets.add(
      SizedBox(
        width: double.infinity,
        child: ElevatedButton(
          onPressed: () => submitFilters(),
          child: const Text('Apply'),
        ),
      ),
    );

    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemCount: widgets.length,
        itemBuilder: (_, index) => widgets[index],
        separatorBuilder: (_, __) =>
            const SizedBox(height: spacingBetweenFilters),
      ),
    );
  }
}
