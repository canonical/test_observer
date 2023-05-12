import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact.dart';
import '../models/stage.dart';
import 'dio.dart';

part 'stages.g.dart';

@riverpod
Future<List<Stage>> stages(StagesRef ref, String familyName) async {
  // final dio = ref.watch(dioProvider);

  // final response = await dio.get('/family/$familyName/stages');
  // final List stagesJson = response.data;
  // final stages = stagesJson.map((json) => Stage.fromJson(json)).toList();
  // return stages;

  if (familyName != 'snap') {
    throw Exception('Invalid familyName "$familyName"');
  }

  return Future.delayed(
    const Duration(seconds: 2),
    () => const [
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
}
