import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/family_name.dart';
import '../models/filter.dart';
import 'family_artefacts.dart';

part 'filters.g.dart';

@riverpod
class Filters extends _$Filters {
  @override
  Future<List<Filter>> build(FamilyName family) async {
    final artefacts = await ref.watch(familyArtefactsProvider(family).future);
    final assigneeOptions = {
      for (final a in artefacts.values)
        if (a.assignee != null) a.assignee!.name,
    }.toList();
    assigneeOptions.sort();

    return [
      Filter(
        name: 'Assignee',
        shouldInclude: (artefact) => artefact.assignee?.initials == 'AV',
        options: assigneeOptions,
      ),
    ];
  }
}
