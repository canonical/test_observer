import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import 'artefacts.dart';

part 'artefact.g.dart';

@riverpod
Future<Artefact?> artefact(
  ArtefactRef ref,
  FamilyName family,
  int artefactId,
) async {
  return await ref.watch(
    artefactsProvider(family).selectAsync((artefacts) => artefacts[artefactId]),
  );
}
