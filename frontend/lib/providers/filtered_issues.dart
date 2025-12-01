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

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../routing.dart';
import '../models/issue.dart';
import 'issues_filters.dart';
import 'issues.dart';
import 'search_value.dart';

part 'filtered_issues.g.dart';

@riverpod
class FilteredIssues extends _$FilteredIssues {
  @override
  Future<List<Issue>> build(Uri pageUri) async {
    final filtersState = ref.watch(issuesFiltersProvider(pageUri));
    final searchQuery = ref.watch(
      searchValueProvider(
        pageUri.queryParameters[CommonQueryParameters.searchQuery],
      ),
    );
    final issues = ref.watch(issuesProvider()).value ?? [];

    var filtered = issues;
    if (filtersState.selectedSources.isNotEmpty) {
      filtered = filtered
          .where((i) => filtersState.selectedSources.contains(i.source))
          .toList();
    }
    if (filtersState.selectedProjects.isNotEmpty) {
      filtered = filtered
          .where((i) => filtersState.selectedProjects.contains(i.project))
          .toList();
    }
    if (filtersState.selectedStatuses.isNotEmpty) {
      filtered = filtered
          .where((i) => filtersState.selectedStatuses.contains(i.status))
          .toList();
    }
    if (searchQuery.isNotEmpty) {
      final queryLower = searchQuery.toLowerCase();
      filtered = filtered
          .where((i) => i.title.toLowerCase().contains(queryLower))
          .toList();
    }
    return filtered;
  }
}
