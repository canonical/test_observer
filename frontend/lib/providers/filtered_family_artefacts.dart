import 'dart:collection';

import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/filters.dart';
import '../routing.dart';
import 'family_artefacts.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
LinkedHashMap<int, Artefact> filteredFamilyArtefacts(
  FilteredFamilyArtefactsRef ref,
  Uri pageUri,
) {
  final family = AppRoutes.familyFromUri(pageUri);
  final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;
  final filters =
      emptyArtefactFilters.copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue = pageUri.queryParameters['q'] ?? '';

  final filteredArtefacts = artefacts.values
      .filter(
        (artefact) =>
            _artefactPassesSearch(artefact, searchValue) &&
            filters.doesObjectPassFilters(artefact),
      )
      .toList();

  final sortBy = pageUri.queryParameters['sortBy'];
  final sortDirection = pageUri.queryParameters['direction'];

  int Function(Artefact, Artefact)? compare;
  switch (sortBy) {
    case 'Name':
      compare = (a1, a2) => a1.name.compareTo(a2.name);
      break;
    case 'Version':
      compare = (a1, a2) => a1.version.compareTo(a2.version);
      break;
    case 'Track':
      compare = (a1, a2) => a1.track.compareTo(a2.track);
      break;
    case 'Risk':
      compare = (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
      break;
    case 'Due date':
      compare = (a1, a2) {
        final a1DueDate = a1.dueDate;
        final a2DueDate = a2.dueDate;
        // no due date is always larger
        if (a1DueDate == null) return 1;
        if (a2DueDate == null) return -1;
        return a1DueDate.compareTo(a2DueDate);
      };
      break;
    case 'Reviews remaining':
      compare = (a1, a2) => a1.remainingTestExecutionCount
          .compareTo(a2.remainingTestExecutionCount);
      break;
    case 'Status':
      compare = (a1, a2) => a1.status.name.compareTo(a2.status.name);
      break;
    case 'Assignee':
      compare = (a1, a2) {
        final a1Assignee = a1.assignee?.name;
        final a2Assignee = a2.assignee?.name;
        // no assignee is always larger
        if (a1Assignee == null) return 1;
        if (a2Assignee == null) return -1;
        return a1Assignee.compareTo(a2Assignee);
      };
      break;
    case 'Series':
      compare = (a1, a2) => a1.series.compareTo(a2.series);
      break;
    case 'Repo':
      compare = (a1, a2) => a1.repo.compareTo(a2.repo);
      break;
    case 'Pocket':
      compare = (a1, a2) => a1.stage.name.compareTo(a2.stage.name);
      break;
    default:
      compare = (a1, a2) => a1.name.compareTo(a2.name);
  }

  filteredArtefacts.sort(compare);

  return LinkedHashMap.fromIterable(
    sortDirection == 'DESC' ? filteredArtefacts.reversed : filteredArtefacts,
    key: (a) => a.id,
    value: (a) => a,
  );
}

bool _artefactPassesSearch(Artefact artefact, String searchValue) {
  return artefact.name.toLowerCase().contains(searchValue.toLowerCase());
}
