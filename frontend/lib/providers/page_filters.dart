import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import '../routing.dart';
import 'artefact_builds.dart';
import 'family_artefacts.dart';

part 'page_filters.g.dart';

@riverpod
class PageFilters extends _$PageFilters {
  @override
  Filters build(Uri pageUri) {
    if (AppRoutes.isDashboardPage(pageUri)) {
      final family = AppRoutes.familyFromUri(pageUri);
      final artefacts = ref
          .watch(familyArtefactsProvider(family))
          .requireValue
          .values
          .toList();

      return emptyArtefactFilters
          .copyWithOptionsExtracted(artefacts)
          .copyWithQueryParams(pageUri.queryParametersAll);
    }

    if (AppRoutes.isArtefactPage(pageUri)) {
      final artefactId = AppRoutes.artefactIdFromUri(pageUri);
      final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
      final testExecutions = [
        for (final build in builds)
          for (final testExecution in build.testExecutions) testExecution,
      ];

      return emptyTestExecutionFilters
          .copyWithOptionsExtracted(testExecutions)
          .copyWithQueryParams(pageUri.queryParametersAll);
    }

    throw Exception('Called pageFiltersProvider in unknown page $pageUri');
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
