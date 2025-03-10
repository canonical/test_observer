import '../models/artefact.dart';
import '../models/family_name.dart';
import 'multi_option_filter.dart';

List<MultiOptionFilter<Artefact>> getArtefactFiltersFor(FamilyName family) =>
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
