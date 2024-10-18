import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import 'api.dart';

part 'artefact_builds.g.dart';

@riverpod
Future<List<ArtefactBuild>> artefactBuilds(
  ArtefactBuildsRef ref,
  int artefactId,
) async {
  final api = ref.watch(apiProvider);
  return await api.getArtefactBuilds(artefactId);
}
