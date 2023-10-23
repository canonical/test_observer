import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'dio.dart';

part 'family_artefacts.g.dart';

@riverpod
Future<List<Artefact>> familyArtefacts(
  FamilyArtefactsRef ref,
  FamilyName family,
) async {
  final dio = ref.watch(dioProvider);

  final response = await dio.get('/v1/artefacts?family=${family.name}');
  final List artefactsJson = response.data;
  final artefacts =
      artefactsJson.map((json) => Artefact.fromJson(json)).toList();
  return artefacts;
}
