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
import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
import 'artefact_environment.dart';
import 'environment_review.dart';
import 'family_name.dart';
import 'filter.dart';

part 'filters.freezed.dart';

@freezed
class Filters<T> with _$Filters<T> {
  const Filters._();

  const factory Filters({
    required List<Filter<T>> filters,
  }) = _Filters<T>;

  Filters<T> copyWithFilterOptionValue(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    return copyWith(
      filters: [
        for (final filter in filters)
          if (filter.name == filterName)
            if (optionValue)
              filter.copyWith(
                selectedOptions: filter.selectedOptions.union({optionName}),
              )
            else
              filter.copyWith(
                selectedOptions:
                    filter.selectedOptions.difference({optionName}),
              )
          else
            filter,
      ],
    );
  }

  bool doesObjectPassFilters(T object) =>
      filters.all((filter) => filter.doesObjectPassFilter(object));

  Filters<T> copyWithQueryParams(Map<String, List<String>> queryParams) {
    final newFilters = filters.map((filter) {
      final values = queryParams[filter.name]?.toSet();
      if (values == null || values.isEmpty) return filter;
      return filter.copyWith(
        selectedOptions: values.toSet(),
        detectedOptions: filter.detectedOptions.toSet().union(values).toList()
          ..sort(),
      );
    });

    return copyWith(filters: newFilters.toList());
  }

  Map<String, List<String>> toQueryParams() {
    final queryParams = <String, List<String>>{};
    for (final filter in filters) {
      if (filter.selectedOptions.isNotEmpty) {
        queryParams[filter.name] = filter.selectedOptions.toList();
      }
    }
    return queryParams;
  }

  Filters<T> copyWithOptionsExtracted(List<T> objects) {
    final newFilters = <Filter<T>>[];
    for (final filter in filters) {
      final options = <String>{};
      for (final object in objects) {
        final option = filter.extractOption(object);
        if (option != null) options.add(option);
      }
      newFilters
          .add(filter.copyWith(detectedOptions: options.toList()..sort()));
    }
    return copyWith(filters: newFilters);
  }
}

Filters<Artefact> createEmptyArtefactFilters(FamilyName family) {
  switch (family) {
    case FamilyName.image:
      return emptyImageFilters;
    case FamilyName.snap:
      return emptySnapFilters;
    case FamilyName.deb:
      return emptyDebFilters;
    case FamilyName.charm:
      return emptyCharmFilters;
  }
}

final emptyCharmFilters = Filters<Artefact>(
  filters: [
    _artefactAssigneeFilter,
    _artefactStatusFilter,
    _artefactDueDateFilter,
    _artefactRiskFilter,
  ],
);

final emptyDebFilters = Filters<Artefact>(
  filters: [
    _artefactAssigneeFilter,
    _artefactStatusFilter,
    _artefactDueDateFilter,
    _artefactSeriesFilter,
    _artefactPocketFilter,
  ],
);

final emptySnapFilters = Filters<Artefact>(
  filters: [
    _artefactAssigneeFilter,
    _artefactStatusFilter,
    _artefactDueDateFilter,
    _artefactRiskFilter,
  ],
);

final emptyImageFilters = Filters<Artefact>(
  filters: [
    _artefactOSFilter,
    _artefactReleaseFilter,
    _artefactOwnerFilter,
    _artefactAssigneeFilter,
    _artefactStatusFilter,
    _artefactDueDateFilter,
  ],
);

final emptyArtefactEnvironmentsFilters = Filters<ArtefactEnvironment>(
  filters: [
    Filter<ArtefactEnvironment>(
      name: 'Review status',
      extractOption: (environment) =>
          switch (environment.review.reviewDecision) {
        [] => 'Undecided',
        [EnvironmentReviewDecision.rejected] => 'Rejected',
        [...] => 'Approved',
      },
    ),
    Filter<ArtefactEnvironment>(
      name: 'Last execution status',
      extractOption: (environment) =>
          environment.runsDescending.firstOrNull?.status.name,
    ),
  ],
);

Filter<Artefact> _artefactAssigneeFilter = Filter<Artefact>(
  name: 'Assignee',
  extractOption: (artefact) => artefact.assignee.name,
);

Filter<Artefact> _artefactStatusFilter = Filter<Artefact>(
  name: 'Status',
  extractOption: (artefact) => artefact.status.name,
);

Filter<Artefact> _artefactDueDateFilter = Filter<Artefact>(
  name: 'Due date',
  extractOption: (artefact) {
    final now = DateTime.now();
    final dueDate = artefact.dueDate;

    if (dueDate == null) return 'No due date';
    if (dueDate.isBefore(now)) return 'Overdue';

    final daysDueIn = now.difference(dueDate).inDays;
    if (daysDueIn >= 7) return 'More than a week';
    return 'Within a week';
  },
);

Filter<Artefact> _artefactRiskFilter = Filter<Artefact>(
  name: 'Risk',
  extractOption: (artefact) => artefact.stage.name,
);

Filter<Artefact> _artefactSeriesFilter = Filter<Artefact>(
  name: 'Series',
  extractOption: (artefact) => artefact.series,
);

Filter<Artefact> _artefactOSFilter = Filter<Artefact>(
  name: 'OS type',
  extractOption: (artefact) => artefact.os,
);

Filter<Artefact> _artefactReleaseFilter = Filter<Artefact>(
  name: 'Release',
  extractOption: (artefact) => artefact.release,
);

Filter<Artefact> _artefactOwnerFilter = Filter<Artefact>(
  name: 'Owner',
  extractOption: (artefact) => artefact.owner,
);

Filter<Artefact> _artefactPocketFilter = Filter<Artefact>(
  name: 'Pocket',
  extractOption: (artefact) => artefact.stage.name,
);
