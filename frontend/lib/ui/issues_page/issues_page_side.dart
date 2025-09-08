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

import '../../providers/issues_filters.dart';
import '../../routing.dart';
import '../page_filters/multi_select_combobox.dart';
import '../page_filters/checkbox_list_expandable.dart';
import '../page_filters/page_search_bar.dart';
import '../spacing.dart';

class IssuesPageSide extends ConsumerWidget {
  const IssuesPageSide({
    super.key,
    this.searchHint,
    this.width = 300.0,
  });

  final String? searchHint;
  final double width;

  static const spacingBetweenFilters = Spacing.level4;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    void setQueryParam(String key, List<String> values) {
      final pageUri = AppRoutes.uriFromContext(context);
      final params = Map<String, List<String>>.from(pageUri.queryParametersAll);
      if (values.isEmpty) {
        params.remove(key);
      } else {
        params[key] = values;
      }
      final uri = pageUri.replace(queryParameters: params);
      if (uri.toString() != pageUri.toString()) {
        context.go(uri.toString());
      }
    }

    final filtersState =
        ref.watch(issuesFiltersProvider(AppRoutes.uriFromContext(context)));

    final widgets = [
      PageSearchBar(
        hintText: searchHint,
        onSubmitted: (value) {
          setQueryParam(
            CommonQueryParameters.searchQuery,
            value.isEmpty ? [] : [value],
          );
        },
      ),
      CheckboxListExpandable(
        title: 'Source',
        options: filtersState.possibleSources
            .map(
              (source) => (
                name: source.name,
                isSelected: filtersState.selectedSources.contains(source),
              ),
            )
            .toList(),
        onChanged: (option, isSelected) {
          final newSources = Set<String>.from(
            filtersState.selectedSources.map((s) => s.name),
          );
          isSelected ? newSources.add(option) : newSources.remove(option);
          setQueryParam(IssuesFilters.sourceParam, newSources.toList());
        },
      ),
      CheckboxListExpandable(
        title: 'Status',
        options: filtersState.possibleStatuses
            .map(
              (status) => (
                name: status.name,
                isSelected: filtersState.selectedStatuses.contains(status),
              ),
            )
            .toList(),
        onChanged: (option, isSelected) {
          final newStatuses = Set<String>.from(
            filtersState.selectedStatuses.map((s) => s.name),
          );
          isSelected ? newStatuses.add(option) : newStatuses.remove(option);
          setQueryParam(IssuesFilters.statusParam, newStatuses.toList());
        },
      ),
      MultiSelectCombobox(
        title: 'Project',
        allOptions: filtersState.possibleProjects.toList(),
        initialSelected: filtersState.selectedProjects,
        onChanged: (option, isSelected) {
          final newProjects = Set<String>.from(filtersState.selectedProjects);
          isSelected ? newProjects.add(option) : newProjects.remove(option);
          setQueryParam(IssuesFilters.projectParam, newProjects.toList());
        },
      ),
    ];

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
