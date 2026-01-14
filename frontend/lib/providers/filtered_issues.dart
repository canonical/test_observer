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
import 'issues_pagination.dart';

part 'filtered_issues.g.dart';

@riverpod
class FilteredIssues extends _$FilteredIssues {
  List<Issue> _accumulatedIssues = [];
  int _lastOffset = -1;
  String? _lastFiltersKey;

  String _getFiltersKey(IssuesFiltersState filtersState, String searchQuery) {
    // Create a unique key based on filter selections and search
    final sources = filtersState.selectedSources.map((s) => s.name).toList()..sort();
    final projects = filtersState.selectedProjects.toList()..sort();
    final statuses = filtersState.selectedStatuses.map((s) => s.name).toList()..sort();
    return '${sources.join(',')}|${projects.join(',')}|${statuses.join(',')}|$searchQuery';
  }

  @override
  Future<List<Issue>> build(Uri pageUri) async {
    final filtersState = ref.watch(issuesFiltersProvider(pageUri));
    final searchQuery = ref.watch(
      searchValueProvider(
        pageUri.queryParameters[CommonQueryParameters.searchQuery],
      ),
    );
    final paginationState = ref.watch(issuesPaginationProvider(pageUri));

    // Check if filters or search changed
    final currentFiltersKey = _getFiltersKey(filtersState, searchQuery);
    final filtersChanged = _lastFiltersKey != null && _lastFiltersKey != currentFiltersKey;
    _lastFiltersKey = currentFiltersKey;

    // Reset accumulated issues if offset is back to 0, went backwards, or filters changed
    if (paginationState.offset == 0 || paginationState.offset < _lastOffset || filtersChanged) {
      _accumulatedIssues = [];
    }

    // Convert filter state to API parameters
    // Single-value filters are passed to API for server-side filtering
    // Multi-value filters fall back to client-side filtering
    final source = filtersState.selectedSources.length == 1
        ? filtersState.selectedSources.first.name
        : null;
    final project = filtersState.selectedProjects.length == 1
        ? filtersState.selectedProjects.first
        : null;
    final status = filtersState.selectedStatuses.length == 1
        ? filtersState.selectedStatuses.first.name
        : null;

    // Fetch issues from API with filters
    final issues = await ref.watch(
      issuesProvider(
        source: source,
        project: project,
        status: status,
        limit: paginationState.limit,
        offset: paginationState.offset,
        q: searchQuery.isNotEmpty ? searchQuery : null,
      ).future,
    );

    // Apply client-side filtering for multi-select cases
    // This handles the edge case where users select multiple sources/projects/statuses
    var filtered = issues;
    if (filtersState.selectedSources.length > 1) {
      filtered = filtered
          .where((i) => filtersState.selectedSources.contains(i.source))
          .toList();
    }
    if (filtersState.selectedProjects.length > 1) {
      filtered = filtered
          .where((i) => filtersState.selectedProjects.contains(i.project))
          .toList();
    }
    if (filtersState.selectedStatuses.length > 1) {
      filtered = filtered
          .where((i) => filtersState.selectedStatuses.contains(i.status))
          .toList();
    }

    // Accumulate issues instead of replacing them
    if (paginationState.offset > 0) {
      // Add new issues to accumulated list, avoiding duplicates
      final existingIds = _accumulatedIssues.map((i) => i.id).toSet();
      final newIssues = filtered.where((i) => !existingIds.contains(i.id)).toList();
      _accumulatedIssues = [..._accumulatedIssues, ...newIssues];
    } else {
      _accumulatedIssues = filtered;
    }

    _lastOffset = paginationState.offset;
    return _accumulatedIssues;
  }
}
