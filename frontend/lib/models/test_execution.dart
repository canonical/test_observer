import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';

import 'environment.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
class TestExecution with _$TestExecution {
  const factory TestExecution({
    required int id,
    @JsonKey(name: 'jenkins_link') required String? jenkinsLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);
}

enum TestExecutionStatus {
  @JsonValue('FAILED')
  failed,
  @JsonValue('IN_PROGRESS')
  inProgress,
  @JsonValue('PASSED')
  passed,
  @JsonValue('UNKNOWN')
  unknown;

  String get name {
    switch (this) {
      case inProgress:
        return 'In Progress';
      case passed:
        return 'Passed';
      case failed:
        return 'Failed';
      case unknown:
        return 'Unknown';
    }
  }

  Icon get icon {
    const size = 20.0;
    switch (this) {
      case inProgress:
        return const Icon(YaruIcons.refresh, size: size);
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case unknown:
        return const Icon(YaruIcons.question, size: size);
    }
  }
}
