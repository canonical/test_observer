import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/family_name.dart';
import '../models/stage_name.dart';
import 'artefacts.dart';

part 'stage_artefacts.g.dart';

@riverpod
Future<List<Artefact>> stageArtefacts(
  StageArtefactsRef ref,
  FamilyName family,
  StageName stage,
) async {
  final artefacts = await ref.watch(
    artefactsProvider(family).selectAsync(
      (artefacts) => [
        for (final artefact in artefacts.values)
          if (artefact.stage == stage) artefact,
      ],
    ),
  );

  return artefacts;
}
