import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'family_artefacts.dart';
import 'filters.dart';

part 'filtered_artefacts.g.dart';

@riverpod
Future<Map<int, Artefact>> filteredArtefacts(
  FilteredArtefactsRef ref,
  FamilyName family,
) async {
  final artefacts = await ref.watch(familyArtefactsProvider(family).future);
  final filters = await ref.watch(filtersProvider(family).future);
  final filteredArtefacts = artefacts.filterValues(
    (artefact) => filters.all((filter) => filter.shouldInclude(artefact)),
  );
  return filteredArtefacts;
}
