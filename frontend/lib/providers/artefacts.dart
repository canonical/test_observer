import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'dio.dart';

part 'artefacts.g.dart';

@riverpod
class Artefacts extends _$Artefacts {
  @override
  Future<Map<int, Artefact>> build(FamilyName family) async {
    final dio = ref.watch(dioProvider);
    final response = await dio
        .get('/v1/artefacts', queryParameters: {'family': family.name});
    final artefacts = {
      for (final json in response.data)
        json['id'] as int: Artefact.fromJson(json),
    };
    return artefacts;
  }

  Future<void> changeArtefactStatus(
    int artefactId,
    ArtefactStatus newStatus,
  ) async {
    final dio = ref.watch(dioProvider);

    final response = await dio.patch(
      '/v1/artefacts/$artefactId',
      data: {'status': newStatus.toJson()},
    );

    final previousState = await future;
    final artefact = Artefact.fromJson(response.data);
    state = AsyncData({...previousState, artefact.id: artefact});
  }
}
