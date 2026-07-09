// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import '../models/artefact.dart';
import '../routing.dart';

enum ArtefactSortingQuery {
  name,
  version,
  track,
  risk,
  branch,
  dueDate,
  reviewsRemaining,
  status,
  reviewer,
  assignee, // deprecated alias for reviewer, kept for URL backwards-compatibility
  series,
  source,
  repo,
  pocket,
  os,
  release,
  owner,
}

void sortArtefacts(
  Map<String, String> queryParameters,
  List<Artefact> artefacts,
) {
  final sortBy = queryParameters[CommonQueryParameters.sortBy] ?? '';
  final sortDirection = queryParameters[CommonQueryParameters.sortDirection];

  ArtefactSortingQuery sortByParsed = ArtefactSortingQuery.name;
  try {
    sortByParsed = ArtefactSortingQuery.values.byName(sortBy);
  } on ArgumentError {
    // use default
  }

  final compare = _getArtefactCompareFunction(sortByParsed);

  if (sortDirection == SortDirection.desc.name) {
    artefacts.sort((a1, a2) => compare(a2, a1));
  } else {
    artefacts.sort(compare);
  }
}

int Function(Artefact, Artefact) _getArtefactCompareFunction(
  ArtefactSortingQuery sortByParsed,
) {
  switch (sortByParsed) {
    case ArtefactSortingQuery.name:
      return (a1, a2) => a1.name.compareTo(a2.name);
    case ArtefactSortingQuery.version:
      return (a1, a2) => a1.version.compareTo(a2.version);
    case ArtefactSortingQuery.track:
      return (a1, a2) => a1.track.compareTo(a2.track);
    case ArtefactSortingQuery.risk:
      return (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
    case ArtefactSortingQuery.branch:
      return (a1, a2) => a1.branch.compareTo(a2.branch);
    case ArtefactSortingQuery.dueDate:
      return (a1, a2) {
        final a1DueDate = a1.dueDate;
        final a2DueDate = a2.dueDate;
        // no due date is always larger
        if (a1DueDate == null) return 1;
        if (a2DueDate == null) return -1;
        return a1DueDate.compareTo(a2DueDate);
      };
    case ArtefactSortingQuery.reviewsRemaining:
      return (a1, a2) => a1.remainingTestExecutionCount
          .compareTo(a2.remainingTestExecutionCount);
    case ArtefactSortingQuery.status:
      return (a1, a2) => a1.status.name.compareTo(a2.status.name);
    case ArtefactSortingQuery.reviewer:
    case ArtefactSortingQuery.assignee: // deprecated alias for reviewer
      return (a1, a2) {
        if (a1.reviewers.isEmpty && a2.reviewers.isEmpty) return 0;
        if (a1.reviewers.isEmpty) return 1;
        if (a2.reviewers.isEmpty) return -1;
        final countComparison =
            a1.reviewers.length.compareTo(a2.reviewers.length);
        if (countComparison != 0) return countComparison;
        return a1.reviewers.first.name.compareTo(a2.reviewers.first.name);
      };
    case ArtefactSortingQuery.series:
      return (a1, a2) => a1.series.compareTo(a2.series);
    case ArtefactSortingQuery.repo:
      return (a1, a2) => a1.repo.compareTo(a2.repo);
    case ArtefactSortingQuery.source:
      return (a1, a2) => a1.source.compareTo(a2.source);
    case ArtefactSortingQuery.pocket:
      return (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
    case ArtefactSortingQuery.os:
      return (a1, a2) => a1.os.compareTo(a2.os);
    case ArtefactSortingQuery.release:
      return (a1, a2) => a1.release.compareTo(a2.release);
    case ArtefactSortingQuery.owner:
      return (a1, a2) => a1.owner.compareTo(a2.owner);
  }
}
