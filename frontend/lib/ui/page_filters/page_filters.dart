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

class PageFiltersView extends ConsumerWidget {
  const PageFiltersView({super.key, this.searchHint, this.width = 300.0});

  final String? searchHint;
  final double width;

  static const spacingBetweenFilters = Spacing.level4;

  // Global key for environment combobox focus
  static final GlobalKey<MultiSelectComboboxState> environmentComboboxKey =
      GlobalKey<MultiSelectComboboxState>();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final searchQuery =
        pageUri.queryParameters[CommonQueryParameters.searchQuery];
    final filters = ref.watch(pageFiltersProvider(pageUri));
    final isArtefactPage = AppRoutes.isArtefactPage(pageUri);

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

    // Build the list of widgets
    final widgets = <Widget>[];

    // Only add search bar for dashboard pages (not artefact pages)
    if (!isArtefactPage) {
      widgets.add(
        PageSearchBar(
          hintText: searchHint,
          onSubmitted: (_) => submitFilters(),
        ),
      );
    }

    // For artefact pages, handle Environment and Test plan as comboboxes
    if (isArtefactPage) {
      // Find and handle Environment filter
      FilterState? envFilter;
      try {
        envFilter = filters.firstWhere((f) => f.name == 'Environment');
      } catch (e) {
        envFilter = null;
      }

      if (envFilter != null) {
        final environmentOptions =
            envFilter.options.map((e) => e.name).toList();
        widgets.add(
          MultiSelectCombobox(
            key: environmentComboboxKey,
            title: 'Environment',
            allOptions: environmentOptions,
            maxSuggestions: 10, // Explicit limit for environments
            onChanged: (option, isSelected) => ref
                .read(pageFiltersProvider(pageUri).notifier)
                .onChanged(envFilter!.name, option, isSelected),
          ),
        );
      }

      // Find and handle Test plan filter
      FilterState? planFilter;
      try {
        planFilter = filters.firstWhere((f) => f.name == 'Test plan');
      } catch (e) {
        planFilter = null;
      }

      if (planFilter != null) {
        final planOptions = planFilter.options.map((e) => e.name).toList();
        widgets.add(
          MultiSelectCombobox(
            title: 'Test plan',
            allOptions: planOptions,
            maxSuggestions: 10, // Explicit limit for test plans
            onChanged: (option, isSelected) => ref
                .read(pageFiltersProvider(pageUri).notifier)
                .onChanged(planFilter!.name, option, isSelected),
          ),
        );
      }
    }

    // Add remaining filters as regular checkbox lists
    final regularFilters = isArtefactPage
        ? filters
            .where((f) => f.name != 'Environment' && f.name != 'Test plan')
            .toList()
        : filters;

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

    // Add apply button last
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
