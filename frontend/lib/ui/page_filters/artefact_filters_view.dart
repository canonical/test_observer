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
import '../../routing.dart';
import 'checkbox_list_expandable.dart';
import 'multi_select_combobox.dart';
import '../spacing.dart';

class ArtefactFiltersView extends ConsumerWidget {
  const ArtefactFiltersView({super.key, this.width = 300.0});

  final double width;

  // Global key for environment combobox focus (for Ctrl+F)
  static final GlobalKey<MultiSelectComboboxState> environmentComboboxKey =
      GlobalKey<MultiSelectComboboxState>();

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final filters = ref.watch(pageFiltersProvider(pageUri));

    void submitFilters() {
      final queryParams = {
        ...ref.read(pageFiltersProvider(pageUri).notifier).toQueryParams(),
      };
      context.go(pageUri.replace(queryParameters: queryParams).toString());
    }

    final widgets = <Widget>[];

    // Process filters: Environment and Test plan as comboboxes, others as checkboxes
    final comboboxFilters = <FilterState>[];
    final regularFilters = <FilterState>[];

    for (final filter in filters) {
      if (filter.name == 'Environment' || filter.name == 'Test plan') {
        comboboxFilters.add(filter);
      } else {
        regularFilters.add(filter);
      }
    }

    // Sort combobox filters: Environment first, then Test plan
    comboboxFilters.sort((a, b) {
      if (a.name == 'Environment') return -1;
      if (b.name == 'Environment') return 1;
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
        MultiSelectCombobox<String>(
          key: key,
          title: filter.name,
          allOptions: options,
          itemToString: (option) => option,
          initialSelected: initialSelected,
          maxSuggestions: 10,
          onChanged: (option, isSelected) {
            // Update the filter state
            ref
                .read(pageFiltersProvider(pageUri).notifier)
                .onChanged(filter.name, option, isSelected);

            // Immediately update the URL with new filter state
            final queryParams = {
              ...ref
                  .read(pageFiltersProvider(pageUri).notifier)
                  .toQueryParams(),
            };

            // Navigate to new URL immediately
            context
                .go(pageUri.replace(queryParameters: queryParams).toString());
          },
        ),
      );
    }

    // Add regular checkbox filters
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
