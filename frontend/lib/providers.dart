import 'package:riverpod_annotation/riverpod_annotation.dart';

import 'models/artefact.dart';
import 'models/artefact_family.dart';
import 'models/stage.dart';

part 'providers.g.dart';

@riverpod
Future<ArtefactFamily> fetchFamily(FetchFamilyRef ref, String familyName) {
  if (familyName != 'snaps') {
    throw Exception('Invalid familyName "$familyName"');
  }

  return Future.delayed(
    const Duration(seconds: 2),
    () => const ArtefactFamily(
      name: 'Family',
      stages: [
        Stage(
          name: 'Stage 1',
          artefacts: [
            Artefact(name: 'Artefact 1'),
            Artefact(name: 'Artefact 2'),
            Artefact(name: 'Artefact 3'),
            Artefact(name: 'Artefact 4'),
          ],
        ),
        Stage(
          name: 'Stage 2',
          artefacts: [
            Artefact(name: 'Artefact 11'),
            Artefact(name: 'Artefact 12'),
          ],
        ),
        Stage(
          name: 'Stage 3',
          artefacts: [
            Artefact(name: 'Artefact 21'),
            Artefact(name: 'Artefact 22'),
            Artefact(name: 'Artefact 23'),
            Artefact(name: 'Artefact 24'),
            Artefact(name: 'Artefact 24'),
          ],
        ),
        Stage(
          name: 'Stage 4',
          artefacts: [],
        ),
      ],
    ),
  );
}
