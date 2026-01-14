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
import 'package:freezed_annotation/freezed_annotation.dart';

import '../models/issue.dart';
import 'issues.dart';

part 'issues_filters.freezed.dart';
part 'issues_filters.g.dart';

@freezed
abstract class IssuesFiltersState with _$IssuesFiltersState {
  const factory IssuesFiltersState({
    @Default({}) Set<IssueSource> possibleSources,
    @Default({}) Set<String> possibleProjects,
    @Default({}) Set<IssueStatus> possibleStatuses,
    @Default({}) Set<IssueSource> selectedSources,
    @Default({}) Set<String> selectedProjects,
    @Default({}) Set<IssueStatus> selectedStatuses,
  }) = _IssuesFiltersState;
}

@riverpod
class IssuesFilters extends _$IssuesFilters {
  static const sourceParam = 'source';
  static const projectParam = 'project';
  static const statusParam = 'status';

  @override
  IssuesFiltersState build(Uri pageUri) {
    final issues = ref.watch(issuesProvider()).value ?? [];
    final params = pageUri.queryParametersAll;

    // Sources
    final selectedSources = IssueSource.values
        .where((v) => (params[sourceParam] ?? []).contains(v.name))
        .toSet();
    final possibleSources = issues.map((i) => i.source).toSet();
    final validSelectedSources = selectedSources.intersection(possibleSources);

    // Statuses
    final possibleStatuses = IssueStatus.values.toSet();
    final selectedStatuses = IssueStatus.values
        .where((v) => (params[statusParam] ?? []).contains(v.name))
        .toSet();
    final validSelectedStatuses =
        selectedStatuses.intersection(possibleStatuses);

    // Projects
    final selectedProjects = (params[projectParam] ?? []).toSet();
    var filtered = issues;
    if (selectedSources.isNotEmpty) {
      filtered = filtered
          .where((i) => validSelectedSources.contains(i.source))
          .toList();
    }
    if (validSelectedStatuses.isNotEmpty) {
      filtered = filtered
          .where((i) => validSelectedStatuses.contains(i.status))
          .toList();
    }
    final possibleProjects = filtered.map((i) => i.project).toSet();
    final validSelectedProjects =
        selectedProjects.intersection(possibleProjects);

    return IssuesFiltersState(
      possibleSources: possibleSources,
      possibleProjects: possibleProjects,
      possibleStatuses: possibleStatuses,
      selectedSources: validSelectedSources,
      selectedProjects: validSelectedProjects,
      selectedStatuses: validSelectedStatuses,
    );
  }
}
