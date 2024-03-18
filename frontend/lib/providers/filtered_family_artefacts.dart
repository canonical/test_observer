import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/filters.dart';
import '../routing.dart';
import 'family_artefacts.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
Map<int, Artefact> filteredFamilyArtefacts(
  FilteredFamilyArtefactsRef ref,
  Uri pageUri,
) {
  final family = AppRoutes.familyFromUri(pageUri);
  final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;
  final filters =
      emptyArtefactFilters.copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue = pageUri.queryParameters['q'] ?? '';

  return artefacts.filterValues(
    (artefact) =>
        _artefactPassesSearch(artefact, searchValue) &&
        filters.doesObjectPassFilters(artefact),
  );
}

bool _artefactPassesSearch(Artefact artefact, String searchValue) {
  return artefact.name.toLowerCase().contains(searchValue.toLowerCase());
}
