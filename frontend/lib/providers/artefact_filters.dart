import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filter.dart';
import 'family_artefacts.dart';

part 'artefact_filters.g.dart';

@riverpod
class ArtefactFilters extends _$ArtefactFilters {
  @override
  List<Filter<Artefact>> build(FamilyName family) {
    final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;

    return [
      Filter<Artefact>(
        name: 'Assignee',
        retrieveOption: _extractAssigneeName,
        options: _extractOptions(artefacts, _extractAssigneeName),
      ),
      Filter<Artefact>(
        name: 'Status',
        retrieveOption: _extractStatusName,
        options: _extractOptions(artefacts, _extractStatusName),
      ),
    ];
  }

  void handleFilterOptionChange(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    final filters = state;
    final newFilters = [
      for (final filter in filters)
        if (filter.name == filterName)
          filter.copyWithOptionValue(optionName, optionValue)
        else
          filter,
    ];
    state = newFilters;
  }

  String? _extractAssigneeName(Artefact artefact) => artefact.assignee?.name;
  String _extractStatusName(Artefact artefact) => artefact.status.name;

  List<({String name, bool value})> _extractOptions(
    Map<int, Artefact> artefacts,
    String? Function(Artefact) extractor,
  ) {
    final names = <dynamic>{};
    for (final artefact in artefacts.values) {
      final name = extractor(artefact);
      if (name != null) names.add(name);
    }

    return [
      for (final name in names.toList().sorted()) (name: name, value: false),
    ];
  }
}
