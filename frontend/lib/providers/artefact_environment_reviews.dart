import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/environment_review.dart';
import 'api.dart';

part 'artefact_environment_reviews.g.dart';

@riverpod
class ArtefactEnvironmentReviews extends _$ArtefactEnvironmentReviews {
  @override
  Future<List<EnvironmentReview>> build(int artefactId) async {
    final api = ref.watch(apiProvider);
    return api.getArtefactEnvironmentReviews(artefactId);
  }
}
