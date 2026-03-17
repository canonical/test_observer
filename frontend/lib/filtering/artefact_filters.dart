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

final _artefactAssigneeFilter = createFilterFromExtractor<Artefact>(
  'Assignee',
  (artefact) => artefact.assignee.name,
);

final _artefactStatusFilter = createFilterFromExtractor<Artefact>(
  'Status',
  (artefact) => artefact.status.name,
);

final _artefactDueDateFilter = createFilterFromExtractor<Artefact>(
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

final _artefactRiskFilter = createFilterFromExtractor<Artefact>(
  'Risk',
  (artefact) => artefact.stage.name,
);

final _artefactSeriesFilter = createFilterFromExtractor<Artefact>(
  'Series',
  (artefact) => artefact.series,
);

final _artefactOSFilter = createFilterFromExtractor<Artefact>(
  'OS type',
  (artefact) => artefact.os,
);

final _artefactReleaseFilter = createFilterFromExtractor<Artefact>(
  'Release',
  (artefact) => artefact.release,
);

final _artefactOwnerFilter = createFilterFromExtractor<Artefact>(
  'Owner',
  (artefact) => artefact.owner,
);

final _artefactPocketFilter = createFilterFromExtractor<Artefact>(
  'Pocket',
  (artefact) => artefact.stage.name,
);
