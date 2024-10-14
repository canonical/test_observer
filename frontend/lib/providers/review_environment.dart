import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/environment_review.dart';
import 'artefact.dart';
import 'artefact_environment_reviews.dart';

part 'review_environment.g.dart';

@riverpod
class ReviewEnvironment extends _$ReviewEnvironment {
  @override
  Future<void> build() async {
    return;
  }

  Future<void> review(
    EnvironmentReview review,
    int artefactId,
  ) async {
    await ref
        .read(artefactEnvironmentReviewsProvider(artefactId).notifier)
        .updateReview(review);

    final environmentReviews =
        await ref.read(artefactEnvironmentReviewsProvider(artefactId).future);

    final newCompletedEnvironmentReviewsCount = environmentReviews.fold(
      0,
      (count, review) => count + (review.reviewDecision.isEmpty ? 0 : 1),
    );

    await ref
        .read(artefactProvider(artefactId).notifier)
        .updateCompletedEnvironmentReviewsCount(
          newCompletedEnvironmentReviewsCount,
        );
  }
}
