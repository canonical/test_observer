import 'package:freezed_annotation/freezed_annotation.dart';

import 'test_execution.dart';

part 'artefact_build.freezed.dart';

@freezed
class ArtefactBuild with _$ArtefactBuild {
  const ArtefactBuild._();

  const factory ArtefactBuild({
    required int id,
    required String architecture,
    required int? revision,
    required List<TestExecution> testExecutions,
  }) = _ArtefactBuild;

  factory ArtefactBuild.fromJson(Map<String, Object?> json) {
    return ArtefactBuild(
      architecture: json['architecture'] as String,
      id: json['id'] as int,
      revision: json['revision'] as int?,
      testExecutions: [
        for (final te in json['test_executions'] as List)
          TestExecution.fromJson({...te, 'artefact_build_id': json['id']}),
      ],
    );
  }
}
