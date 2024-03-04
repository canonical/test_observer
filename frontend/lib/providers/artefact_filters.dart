import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filter.dart';
import 'family_artefacts.dart';

part 'artefact_filters.g.dart';

@riverpod
class ArtefactFilters extends _$ArtefactFilters {
  @override
  List<Filter> build(FamilyName family) {
    final artefacts = ref.watch(familyArtefactsProvider(family)).requireValue;

    return [
      Filter(
        name: 'Assignee',
        retrieveOption: (artefact) => artefact.assignee?.name,
        options: _extractAssigneeOptions(artefacts),
      ),
      Filter(
        name: 'Status',
        retrieveOption: (artefact) => artefact.status.name,
        options: _extractStatusOptions(artefacts),
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
          _createNewFilter(filter, optionName, optionValue)
        else
          filter,
    ];
    state = newFilters;
  }

  List<({String name, bool value})> _extractAssigneeOptions(
    Map<int, Artefact> artefacts,
  ) {
    final assigneeNames = {
      for (final a in artefacts.values)
        if (a.assignee != null) a.assignee!.name,
    }.toList();
    assigneeNames.sort();
    return [for (final name in assigneeNames) (name: name, value: false)];
  }

  List<({String name, bool value})> _extractStatusOptions(
    Map<int, Artefact> artefacts,
  ) {
    final assigneeNames =
        {for (final a in artefacts.values) a.status.name}.toList();
    assigneeNames.sort();
    return [for (final name in assigneeNames) (name: name, value: false)];
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
