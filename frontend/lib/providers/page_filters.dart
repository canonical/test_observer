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

import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../filtering/artefact_filters.dart';
import '../filtering/enriched_test_execution_filters.dart';
import '../routing.dart';
import 'enriched_test_executions.dart';
import 'family_artefacts.dart';
import '../filtering/multi_option_filter.dart';

part 'page_filters.g.dart';

typedef FilterOptionState = ({String name, bool isSelected});

typedef FilterState = ({String name, List<FilterOptionState> options});

@riverpod
class PageFilters extends _$PageFilters {
  @override
  List<FilterState> build(Uri pageUri) {
    final queryParams = pageUri.queryParametersAll;
    if (AppRoutes.isDashboardPage(pageUri)) {
      final family = AppRoutes.familyFromUri(pageUri);
      final artefacts = ref.watch(familyArtefactsProvider(family)).value ?? {};
      return _createFiltersState(
        getArtefactFiltersFor(family),
        queryParams,
        artefacts.values.toList(),
      );
    }

    if (AppRoutes.isArtefactPage(pageUri)) {
      final artefactId = AppRoutes.artefactIdFromUri(pageUri);
      final enrichedExecutions =
          ref.watch(enrichedTestExecutionsProvider(artefactId)).value ?? [];
      return _createFiltersState(
        enrichedTestExecutionFilters,
        queryParams,
        enrichedExecutions,
      );
    }

    throw Exception('Called filtersStateProvider in unknown page $pageUri');
  }

  List<FilterState> _createFiltersState<T>(
    List<MultiOptionFilter<T>> filters,
    Map<String, List<String>> queryParams,
    List<T> items,
  ) {
    final result = <FilterState>[];
    for (var filter in filters) {
      final selectedOptions = (queryParams[filter.name] ?? []).toSet();
      final allOptions = filter.extractOptions(items).sorted();
      result.add(
        (
          name: filter.name,
          options: allOptions
              .map(
                (option) => (
                  name: option,
                  isSelected: selectedOptions.contains(option),
                ),
              )
              .toList()
        ),
      );
    }
    return result;
  }

  void onChanged(
    String filterName,
    String optionName,
    bool isSelected,
  ) {
    state = state.map((filter) {
      if (filter.name != filterName) {
        return filter;
      }
      return (
        name: filterName,
        options: filter.options
            .map(
              (option) => (
                name: option.name,
                isSelected:
                    option.name == optionName ? isSelected : option.isSelected
              ),
            )
            .toList(),
      );
    }).toList();
  }

  Map<String, List<String>> toQueryParams() => ({
        for (var filter in state)
          filter.name: filter.options
              .filter((option) => option.isSelected)
              .map((option) => option.name)
              .toList(),
      });
}
