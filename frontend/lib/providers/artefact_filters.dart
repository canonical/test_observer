import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filter.dart';
import '../models/filters.dart';
import 'family_artefacts.dart';

part 'artefact_filters.g.dart';

@riverpod
class ArtefactFilters extends _$ArtefactFilters {
  @override
  Filters<Artefact> build(FamilyName family) {
    final artefacts =
        ref.watch(familyArtefactsProvider(family)).requireValue.values.toList();

    return Filters<Artefact>(
      filters: [
        Filter<Artefact>.fromObjects(
          name: 'Assignee',
          extractOption: (artefact) => artefact.assignee?.name,
          objects: artefacts,
        ),
        Filter<Artefact>.fromObjects(
          name: 'Status',
          extractOption: (artefact) => artefact.status.name,
          objects: artefacts,
        ),
      ],
    );
  }

  void handleFilterOptionChange(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    state = state.copyWithFilterOptionValue(
      filterName,
      optionName,
      optionValue,
    );
  }
}
