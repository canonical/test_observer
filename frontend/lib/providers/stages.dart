import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/family_name.dart';
import '../models/stage.dart';
import 'dio.dart';

part 'stages.g.dart';

@riverpod
Future<List<Stage>> stages(StagesRef ref, FamilyName familyName) async {
  final dio = ref.watch(dioProvider);

  final response = await dio.get('/families/${familyName.name}');
  final List stagesJson = response.data;
  final stages = stagesJson.map((json) => Stage.fromJson(json)).toList();
  return stages;
}
