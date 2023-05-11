import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
import 'stage.dart';

part 'family.freezed.dart';

@freezed
class Family with _$Family {
  const factory Family({
    required String name,
    @Default([]) List<Stage> stages,
  }) = _Family;
}

const dummyFamily = Family(
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
);
