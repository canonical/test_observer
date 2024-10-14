import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import '../routing.dart';
import 'artefact_builds.dart';
import 'artefact_environment_reviews.dart';
import 'family_artefacts.dart';

part 'page_filter_groups.g.dart';

@riverpod
class PageFilterGroups extends _$PageFilterGroups {
  @override
  List<FiltersGroup> build(Uri pageUri) {
    if (AppRoutes.isDashboardPage(pageUri)) {
      final family = AppRoutes.familyFromUri(pageUri);
      final artefacts = ref
          .watch(familyArtefactsProvider(family))
          .requireValue
          .values
          .toList();

      return [
        emptyArtefactFilters
            .copyWithOptionsExtracted(artefacts)
            .copyWithQueryParams(pageUri.queryParametersAll),
      ];
    }

    if (AppRoutes.isArtefactPage(pageUri)) {
      final artefactId = AppRoutes.artefactIdFromUri(pageUri);
      final environmentReviews = ref
          .watch(artefactEnvironmentReviewsProvider(artefactId))
          .requireValue;
      final builds = ref.watch(artefactBuildsProvider(artefactId)).requireValue;
      final testExecutions = [
        for (final build in builds)
          for (final testExecution in build.testExecutions) testExecution,
      ];

      return [
        emptyEnvironmentReviewFilters
            .copyWithOptionsExtracted(environmentReviews)
            .copyWithQueryParams(pageUri.queryParametersAll),
        emptyTestExecutionFilters
            .copyWithOptionsExtracted(testExecutions)
            .copyWithQueryParams(pageUri.queryParametersAll),
      ];
    }

    throw Exception('Called pageFiltersProvider in unknown page $pageUri');
  }

  void handleFilterOptionChange(
    int filtersGroupIndex,
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    final filtersListCopy = [...state];
    filtersListCopy[filtersGroupIndex] = filtersListCopy[filtersGroupIndex]
        .copyWithFilterOptionValue(filterName, optionName, optionValue);
    state = filtersListCopy;
  }
}
