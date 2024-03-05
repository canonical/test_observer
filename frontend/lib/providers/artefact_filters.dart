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
          extractOption: _extractAssigneeName,
          objects: artefacts,
        ),
        Filter<Artefact>.fromObjects(
          name: 'Status',
          extractOption: _extractStatusName,
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

  String? _extractAssigneeName(Artefact artefact) => artefact.assignee?.name;
  String _extractStatusName(Artefact artefact) => artefact.status.name;
}
