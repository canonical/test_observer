import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import 'dio.dart';

part 'artefact_notifier.g.dart';

@riverpod
class ArtefactNotifier extends _$ArtefactNotifier {
  @override
  Future<Artefact> build(int artefactId) async {
    final dio = ref.watch(dioProvider);

    final response = await dio.get('/v1/artefacts/$artefactId');
    final artefact = Artefact.fromJson(response.data);
    return artefact;
  }

  Future<void> changeStatus(ArtefactStatus newStatus) async {
    final dio = ref.watch(dioProvider);

    final response = await dio.patch(
      '/v1/artefacts/$artefactId',
      data: {'status': newStatus.toString()},
    );

    state = AsyncData(Artefact.fromJson(response.data));
  }
}
