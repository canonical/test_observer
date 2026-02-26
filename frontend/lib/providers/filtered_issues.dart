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

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../../routing.dart';
import '../models/issue.dart';
import 'issues_filters.dart';
import 'issues.dart';
import 'search_value.dart';
import 'issues_pagination.dart';

part 'filtered_issues.g.dart';

class _FilteredIssuesInternalState {
  final List<Issue> accumulatedIssues;
  final int lastOffset;
  final String? lastFiltersKey;

  const _FilteredIssuesInternalState({
    required this.accumulatedIssues,
    required this.lastOffset,
    this.lastFiltersKey,
  });
}

@riverpod
class FilteredIssues extends _$FilteredIssues {
  _FilteredIssuesInternalState _internalState =
      const _FilteredIssuesInternalState(
    accumulatedIssues: [],
    lastOffset: -1,
    lastFiltersKey: null,
  );

  String _getFiltersKey(IssuesFiltersState filtersState, String searchQuery) {
    // Create a unique key based on filter selections and search
    final sources = filtersState.selectedSources.map((s) => s.name).toList()
      ..sort();
    final projects = filtersState.selectedProjects.toList()..sort();
    final statuses = filtersState.selectedStatuses.map((s) => s.name).toList()
      ..sort();
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
    final filtersChanged = _internalState.lastFiltersKey != null &&
        _internalState.lastFiltersKey != currentFiltersKey;

    // Reset accumulated issues if offset is back to 0, went backwards, or filters changed
    if (paginationState.offset == 0 ||
        paginationState.offset < _internalState.lastOffset ||
        filtersChanged) {
      _internalState = const _FilteredIssuesInternalState(
        accumulatedIssues: [],
        lastOffset: -1,
        lastFiltersKey: null,
      );
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
    List<Issue> accumulatedIssues;
    if (paginationState.offset > 0) {
      // Add new issues to accumulated list, avoiding duplicates
      final existingIds =
          _internalState.accumulatedIssues.map((i) => i.id).toSet();
      final newIssues =
          filtered.where((i) => !existingIds.contains(i.id)).toList();
      accumulatedIssues = [..._internalState.accumulatedIssues, ...newIssues];
    } else {
      accumulatedIssues = filtered;
    }

    // Update internal state
    _internalState = _FilteredIssuesInternalState(
      accumulatedIssues: accumulatedIssues,
      lastOffset: paginationState.offset,
      lastFiltersKey: currentFiltersKey,
    );

    return accumulatedIssues;
  }
}
