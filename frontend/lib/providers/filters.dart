import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filter.dart';
import 'family_artefacts.dart';

part 'filters.g.dart';

@riverpod
class Filters extends _$Filters {
  @override
  List<Filter> build(FamilyName family) {
    final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;

    return [
      Filter(
        name: 'Assignee',
        retrieveArtefactOption: (artefact) => artefact.assignee?.name,
        options: extractAssigneeOptions(artefacts),
      ),
      Filter(
        name: 'Status',
        retrieveArtefactOption: (artefact) => artefact.status.name,
        options: extractStatusOptions(artefacts),
      ),
    ];
  }

  List<({String name, bool value})> extractAssigneeOptions(
    Map<int, Artefact> artefacts,
  ) {
    final assigneeNames = {
      for (final a in artefacts.values)
        if (a.assignee != null) a.assignee!.name,
    }.toList();
    assigneeNames.sort();
    return [for (final name in assigneeNames) (name: name, value: false)];
  }

  List<({String name, bool value})> extractStatusOptions(
    Map<int, Artefact> artefacts,
  ) {
    final assigneeNames =
        {for (final a in artefacts.values) a.status.name}.toList();
    assigneeNames.sort();
    return [for (final name in assigneeNames) (name: name, value: false)];
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
          _createNewFilter(filter, optionName, optionValue)
        else
          filter,
    ];
    state = newFilters;
  }

  Filter _createNewFilter(
    Filter filter,
    String optionName,
    bool optionValue,
  ) {
    return filter.copyWith(
      options: [
        for (final option in filter.options)
          if (option.name == optionName)
            (name: optionName, value: optionValue)
          else
            option,
      ],
    );
  }
}
