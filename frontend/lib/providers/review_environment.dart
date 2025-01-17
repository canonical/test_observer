// Copyright (C) 2024 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
