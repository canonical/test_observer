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

import '../../providers/filters_state.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import 'checkbox_list_expandable.dart';
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
    final filters = ref.watch(filtersStateProvider(pageUri)).value ?? [];

    void submitFilters() {
      final sortBy = pageUri.queryParameters[CommonQueryParameters.sortBy];
      final sortDirection =
          pageUri.queryParameters[CommonQueryParameters.sortDirection];
      final searchValue = ref.read(searchValueProvider(searchQuery)).trim();
      final queryParams = {
        if (searchValue.isNotEmpty)
          CommonQueryParameters.searchQuery: searchValue,
        ...FiltersState.toQueryParams(filters),
        if (sortBy != null) CommonQueryParameters.sortBy: sortBy,
        if (sortDirection != null)
          CommonQueryParameters.sortDirection: sortDirection,
      };
      context.go(
        pageUri.replace(queryParameters: queryParams).toString(),
      );
    }

    return SizedBox(
      width: width,
      child: ListView.separated(
        shrinkWrap: true,
        itemBuilder: (_, i) {
          if (i == 0) {
            return PageSearchBar(
              hintText: searchHint,
              onSubmitted: (_) => submitFilters(),
            );
          }

          if (i == filters.length + 1) {
            return SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => submitFilters(),
                child: const Text('Apply'),
              ),
            );
          }

          return CheckboxListExpandable(
            title: filters[i - 1].name,
            options: filters[i - 1].options,
            onChanged: (option, isSelected) => ref
                .read(filtersStateProvider(pageUri).notifier)
                .onChanged(filters[i - 1].name, option, isSelected),
          );
        },
        separatorBuilder: (_, __) =>
            const SizedBox(height: spacingBetweenFilters),
        itemCount: filters.length + 2,
      ),
    );
  }
}
