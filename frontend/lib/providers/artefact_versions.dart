import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_version.dart';
import 'api.dart';

part 'artefact_versions.g.dart';

@riverpod
Future<List<ArtefactVersion>> artefactVersions(
  ArtefactVersionsRef ref,
  int artefactId,
) async {
  final api = ref.watch(apiProvider);
  return await api.getArtefactVersions(artefactId);
}
