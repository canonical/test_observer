import 'dart:collection';

import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/filters.dart';
import '../routing.dart';
import '../utils/artefact_sorting.dart';
import 'family_artefacts.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
LinkedHashMap<int, Artefact> filteredFamilyArtefacts(
  FilteredFamilyArtefactsRef ref,
  Uri pageUri,
) {
  final family = AppRoutes.familyFromUri(pageUri);
  final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;
  final filters = createEmptyArtefactFilters(family)
      .copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue =
      pageUri.queryParameters[CommonQueryParameters.searchQuery] ?? '';

  final filteredArtefacts = artefacts.values
      .filter(
        (artefact) =>
            _artefactPassesSearch(artefact, searchValue) &&
            filters.doesObjectPassFilters(artefact),
      )
      .toList();

  sortArtefacts(pageUri.queryParameters, filteredArtefacts);

  return LinkedHashMap.fromIterable(
    filteredArtefacts,
    key: (a) => a.id,
    value: (a) => a,
  );
}

bool _artefactPassesSearch(Artefact artefact, String searchValue) {
  return artefact.name.toLowerCase().contains(searchValue.toLowerCase());
}
