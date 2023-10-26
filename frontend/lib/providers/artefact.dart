import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import 'dio.dart';

part 'artefact.g.dart';

@riverpod
Future<Artefact> artefact(ArtefactRef ref, String artefactId) async {
  final dio = ref.watch(dioProvider);

  final response = await dio.get('/v1/artefacts/$artefactId');
  final artefact = Artefact.fromJson(response.data);
  return artefact;
}
