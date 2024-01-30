import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/artefact_filter.dart';
import 'family_artefacts.dart';
import 'artefact_filters.dart';

part 'filtered_family_artefacts.g.dart';

@riverpod
Map<int, Artefact> filteredFamilyArtefacts(
  FilteredFamilyArtefactsRef ref,
  FamilyName family,
) {
  final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;
  final filters = ref.watch(artefactFiltersProvider(family));
  return artefacts.filterValues(
    (artefact) =>
        filters.all((filter) => _artefactPassesFilter(artefact, filter)),
  );
}

bool _artefactPassesFilter(Artefact artefact, ArtefactFilter filter) {
  final noOptionsSelected = filter.options.none((option) => option.value);
  if (noOptionsSelected) return true;
  final selectedOptions = {
    for (final option in filter.options)
      if (option.value) option.name,
  };
  return selectedOptions.contains(filter.retrieveArtefactOption(artefact));
}
