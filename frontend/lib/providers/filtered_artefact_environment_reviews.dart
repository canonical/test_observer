import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/environment_review.dart';
import '../models/filters.dart';
import '../routing.dart';
import 'artefact_environment_reviews.dart';

part 'filtered_artefact_environment_reviews.g.dart';

@riverpod
Future<Iterable<EnvironmentReview>> filteredArtefactEnvironmentReviews(
  FilteredArtefactEnvironmentReviewsRef ref,
  Uri pageUri,
) async {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final filters = emptyEnvironmentReviewFilters
      .copyWithQueryParams(pageUri.queryParametersAll);

  final environmentReviews =
      await ref.watch(artefactEnvironmentReviewsProvider(artefactId).future);

  return environmentReviews
      .filter(filters.doesObjectPassFilters)
      .sortedBy((er) => er.environment.name);
}
