import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'api.dart';

part 'family_artefacts.g.dart';

@riverpod
Future<Map<int, Artefact>> familyArtefacts(
  FamilyArtefactsRef ref,
  FamilyName family,
) {
  final api = ref.watch(apiProvider);
  return api.getFamilyArtefacts(family);
}
