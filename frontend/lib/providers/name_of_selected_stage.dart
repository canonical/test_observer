import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'name_of_selected_stage.g.dart';

@Riverpod(dependencies: [])
String nameOfSelectedStage(NameOfSelectedStageRef ref) {
  throw Exception(
    'Name of selected stage not set yet, need to override provider',
  );
}
