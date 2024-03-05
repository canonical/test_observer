import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filter.dart';
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
  final filters = ref.watch(artefactFiltersProvider(family)).filters;
  final searchValue = ref.watch(searchValueProvider);

  return artefacts.filterValues(
    (artefact) =>
        _artefactPassesSearch(artefact, searchValue) &&
        filters.all((filter) => _artefactPassesFilter(artefact, filter)),
  );
}

bool _artefactPassesFilter(Artefact artefact, Filter<Artefact> filter) {
  final noOptionsSelected = filter.options.none((option) => option.value);
  if (noOptionsSelected) return true;
  final selectedOptions = {
    for (final option in filter.options)
      if (option.value) option.name,
  };
  return selectedOptions.contains(filter.extractOption(artefact));
}

bool _artefactPassesSearch(Artefact artefact, String searchValue) {
  return artefact.name.toLowerCase().contains(searchValue.toLowerCase());
}
