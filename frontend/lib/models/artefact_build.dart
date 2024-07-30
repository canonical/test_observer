import 'package:freezed_annotation/freezed_annotation.dart';

import 'test_execution.dart';

part 'artefact_build.freezed.dart';
part 'artefact_build.g.dart';

@freezed
class ArtefactBuild with _$ArtefactBuild {
  const ArtefactBuild._();

  const factory ArtefactBuild({
    required int id,
    required String architecture,
    required int? revision,
    @JsonKey(name: 'test_executions')
    required List<TestExecution> testExecutions,
  }) = _ArtefactBuild;

  factory ArtefactBuild.fromJson(Map<String, Object?> json) =>
      _$ArtefactBuildFromJson(json);
}
