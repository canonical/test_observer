import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'names_of_stages.g.dart';

@Riverpod(dependencies: [])
List<String> namesOfStages(NamesOfStagesRef ref) {
  throw Exception('Names of stages not set yet, need to override provider');
}
