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
  @JsonValue('NOT_STARTED')
  notStarted,
  @JsonValue('IN_PROGRESS')
  inProgress,
  @JsonValue('PASSED')
  passed,
  @JsonValue('FAILED')
  failed,
  @JsonValue('NOT_TESTED')
  notTested;

  String get name {
    switch (this) {
      case notStarted:
        return 'Not Started';
      case inProgress:
        return 'In Progress';
      case passed:
        return 'Passed';
      case failed:
        return 'Failed';
      case notTested:
        return 'Not Tested';
      default:
        throw Exception('Unknown TestExecutionStatus: $this');
    }
  }

  Icon get icon {
    switch (this) {
      case notStarted:
        return const Icon(YaruIcons.media_play);
      case inProgress:
        return const Icon(YaruIcons.refresh);
      case passed:
        return const Icon(YaruIcons.ok, color: YaruColors.success);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red);
      case notTested:
        return const Icon(YaruIcons.information);
      default:
        throw Exception('Unknown TestExecutionStatus: $this');
    }
  }
}
