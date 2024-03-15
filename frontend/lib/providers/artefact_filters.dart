import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/filters.dart';
import '../routing.dart';
import 'family_artefacts.dart';

part 'artefact_filters.g.dart';

@riverpod
class ArtefactFilters extends _$ArtefactFilters {
  @override
  Filters<Artefact> build(Uri pageUri) {
    final family = pageUri.path.startsWith(AppRoutes.debs)
        ? FamilyName.deb
        : FamilyName.snap;

    final artefacts =
        ref.watch(familyArtefactsProvider(family)).requireValue.values.toList();

    final emptyFilters = getArtefactFilters(artefacts);

    return emptyFilters.copyWithQueryParams(pageUri.queryParametersAll);
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
