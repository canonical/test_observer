import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'family_artefacts.dart';
import 'artefact_filters.dart';
import 'search_value.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
Map<int, Artefact> filteredFamilyArtefacts(
  FilteredFamilyArtefactsRef ref,
  FamilyName family,
) {
  final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;
  final filters = ref.watch(artefactFiltersProvider(family));
  final searchValue = ref.watch(searchValueProvider);

  return artefacts.filterValues(
    (artefact) =>
        _artefactPassesSearch(artefact, searchValue) &&
        filters.doesObjectPassFilters(artefact),
  );
}

bool _artefactPassesSearch(Artefact artefact, String searchValue) {
  return artefact.name.toLowerCase().contains(searchValue.toLowerCase());
}
