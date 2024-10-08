import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart' as artefact_model;
import 'api.dart';

part 'artefact.g.dart';

@riverpod
class Artefact extends _$Artefact {
  @override
  Future<artefact_model.Artefact> build(int artefactId) {
    final api = ref.watch(apiProvider);
    return api.getArtefact(artefactId);
  }

  Future<void> changeArtefactStatus(
    id,
    artefact_model.ArtefactStatus status,
  ) async {
    final api = ref.read(apiProvider);
    final artefact = await api.changeArtefactStatus(artefactId, status);
    state = AsyncData(artefact);
  }

  Future<void> updatecompletedEnvironmentReviewsCount(int count) async {
    final artefact = await future;
    state =
        AsyncData(artefact.copyWith(completedEnvironmentReviewsCount: count));
  }
}
