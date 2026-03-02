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

  static const defaultStatuses = {IssueStatus.open, IssueStatus.unknown};

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

    // Statuses — default to open+unknown when no status param is present
    final possibleStatuses = IssueStatus.values.toSet();
    final selectedStatuses = params.containsKey(statusParam)
        ? IssueStatus.values
            .where((v) => (params[statusParam] ?? []).contains(v.name))
            .toSet()
        : defaultStatuses;
    final validSelectedStatuses =
        selectedStatuses.intersection(possibleStatuses);

    // Projects
    final selectedProjects = (params[projectParam] ?? []).toSet();
    var filtered = issues;
    if (validSelectedSources.isNotEmpty) {
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
