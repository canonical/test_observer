import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'api.dart';

part 'artefact_versions.g.dart';

@riverpod
Future<List<({int artefactId, String version})>> artefactVersions(
  ArtefactVersionsRef ref,
  int artefactId,
) async {
  final api = ref.watch(apiProvider);
  return await api.getArtefactVersions(artefactId);
}
