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
}
