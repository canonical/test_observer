import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import 'dio.dart';

part 'artefact_builds.g.dart';

@riverpod
Future<List<ArtefactBuild>> artefactBuilds(
  ArtefactBuildsRef ref,
  int artefactId,
) async {
  final dio = ref.watch(dioProvider);

  final response = await dio.get('/v1/artefacts/$artefactId/builds');
  final List artefactBuildsJson = response.data;
  final artefactBuilds =
      artefactBuildsJson.map((json) => ArtefactBuild.fromJson(json)).toList();
  return artefactBuilds;
}
