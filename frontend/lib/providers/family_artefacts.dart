import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'api.dart';

part 'family_artefacts.g.dart';

@riverpod
class FamilyArtefacts extends _$FamilyArtefacts {
  @override
  Future<Map<int, Artefact>> build(FamilyName family) async {
    final api = ref.watch(apiProvider);
    return api.getFamilyArtefacts(family);
  }

  Future<void> changeArtefactStatus(
    int artefactId,
    ArtefactStatus newStatus,
  ) async {
    final api = ref.read(apiProvider);
    final artefact = await api.changeArtefactStatus(artefactId, newStatus);

    final previousState = await future;
    state = AsyncData({...previousState, artefact.id: artefact});
  }
}
