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

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'filter.dart';

List<Filter<Artefact>> getArtefactFiltersFor(FamilyName family) =>
    switch (family) {
      FamilyName.snap => [
          _artefactAssigneeFilter,
          _artefactStatusFilter,
          _artefactDueDateFilter,
          _artefactRiskFilter,
        ],
      FamilyName.deb => [
          _artefactAssigneeFilter,
          _artefactStatusFilter,
          _artefactDueDateFilter,
          _artefactSeriesFilter,
          _artefactPocketFilter,
        ],
      FamilyName.charm => [
          _artefactAssigneeFilter,
          _artefactStatusFilter,
          _artefactDueDateFilter,
          _artefactRiskFilter,
        ],
      FamilyName.image => [
          _artefactOSFilter,
          _artefactReleaseFilter,
          _artefactOwnerFilter,
          _artefactAssigneeFilter,
          _artefactStatusFilter,
          _artefactDueDateFilter,
        ],
    };

final _artefactAssigneeFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Assignee',
  (artefact) => artefact.assignee.name,
);

final _artefactStatusFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Status',
  (artefact) => artefact.status.name,
);

final _artefactDueDateFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Due date',
  (artefact) {
    final now = DateTime.now();
    final dueDate = artefact.dueDate;

    if (dueDate == null) return 'No due date';
    if (dueDate.isBefore(now)) return 'Overdue';

    final daysDueIn = now.difference(dueDate).inDays;
    if (daysDueIn >= 7) return 'More than a week';
    return 'Within a week';
  },
);

final _artefactRiskFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Risk',
  (artefact) => artefact.stage.name,
);

final _artefactSeriesFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Series',
  (artefact) => artefact.series,
);

final _artefactOSFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'OS type',
  (artefact) => artefact.os,
);

final _artefactReleaseFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Release',
  (artefact) => artefact.release,
);

final _artefactOwnerFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Owner',
  (artefact) => artefact.owner,
);

final _artefactPocketFilter = createMultiOptionFilterFromExtractor<Artefact>(
  'Pocket',
  (artefact) => artefact.stage.name,
);
