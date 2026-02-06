// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/environment_review.dart';
import 'api.dart';

part 'artefact_environment_reviews.g.dart';

@riverpod
class ArtefactEnvironmentReviews extends _$ArtefactEnvironmentReviews {
  late int _artefactId;

  @override
  Future<List<EnvironmentReview>> build(int artefactId) async {
    _artefactId = artefactId;
    final api = ref.watch(apiProvider);
    return api.getArtefactEnvironmentReviews(artefactId);
  }

  Future<void> updateReview(EnvironmentReview review) async {
    final api = ref.read(apiProvider);
    final updatedReview =
        await api.updateEnvironmentReview(_artefactId, review);
    final reviews = await future;
    state = AsyncData([
      for (final review in reviews)
        review.id == updatedReview.id ? updatedReview : review,
    ]);
  }

  Future<void> bulkUpdateReviews(List<EnvironmentReview> reviews) async {
    final api = ref.read(apiProvider);
    final updatedReviews =
        await api.bulkUpdateEnvironmentReviews(_artefactId, reviews);
    final currentReviews = await future;

    // Create a map of updated reviews by ID for quick lookup
    final updatedReviewMap = {
      for (final review in updatedReviews) review.id: review,
    };

    // Replace the updated reviews in the current list
    state = AsyncData([
      for (final review in currentReviews)
        updatedReviewMap.containsKey(review.id)
            ? updatedReviewMap[review.id]!
            : review,
    ]);
  }
}
