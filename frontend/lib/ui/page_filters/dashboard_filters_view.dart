// Copyright 2025 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/page_filters.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import 'checkbox_list_expandable.dart';
import 'page_search_bar.dart';
import '../spacing.dart';

class DashboardFiltersView extends ConsumerWidget {
  const DashboardFiltersView({super.key, this.searchHint, this.width = 300.0});

  final String? searchHint;
  final double width;

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final searchQuery =
        pageUri.queryParameters[CommonQueryParameters.searchQuery];
    final filters = ref.watch(pageFiltersProvider(pageUri));

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

    // Add search bar first (dashboard-specific feature)
    widgets.add(
      PageSearchBar(
        hintText: searchHint,
        onSubmitted: (_) => submitFilters(),
      ),
    );

    // Add all filters as checkboxes (dashboard shows all filters as checkboxes)
    for (final filter in filters) {
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
