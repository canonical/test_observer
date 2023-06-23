import 'package:freezed_annotation/freezed_annotation.dart';

import 'environment.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
class TestExecution with _$TestExecution {
  const factory TestExecution({
    required int id,
    @JsonKey(name: 'jenkins_link') required String? jenkinsLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required String status,
    required Environment environment,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);
}
