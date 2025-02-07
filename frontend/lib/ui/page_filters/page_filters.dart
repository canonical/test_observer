// Copyright (C) 2023-2025 Canonical Ltd.
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

import '../../models/filter.dart';
import '../../providers/page_filters.dart';
import '../../providers/search_value.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../vanilla/vanilla_button.dart';
import '../vanilla/vanilla_checkbox.dart';
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
    final filters = ref.watch(pageFiltersProvider(pageUri));

    return Padding(
      padding: const EdgeInsets.only(bottom: Spacing.level4),
      child: SizedBox(
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

            if (i == filters.filters.length + 1) {
              return SizedBox(
                width: double.infinity,
                child: VanillaButton(
                  onPressed: () =>
                      submitFilters(ref, searchQuery, pageUri, context),
                  child: const Text('Apply'),
                ),
              );
            }

            return _SideFilter(
              filter: filters.filters[i - 1],
              onOptionChanged: ref
                  .read(pageFiltersProvider(pageUri).notifier)
                  .handleFilterOptionChange,
            );
          },
          separatorBuilder: (_, __) =>
              const SizedBox(height: spacingBetweenFilters),
          itemCount: filters.filters.length + 2,
        ),
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
    final queryParams = {
      if (searchValue.isNotEmpty)
        CommonQueryParameters.searchQuery: searchValue,
      ...ref.read(pageFiltersProvider(pageUri)).toQueryParams(),
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
              VanillaCheckbox(
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
