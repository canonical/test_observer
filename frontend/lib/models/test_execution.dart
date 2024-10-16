import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';

import 'environment.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
class TestExecution with _$TestExecution {
  static const String reviewCommentJsonKey = 'review_comment';
  static const String reviewDecisionJsonKey = 'review_decision';

  const factory TestExecution({
    required int id,
    @JsonKey(name: 'ci_link') required String? ciLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
    @Default(false) @JsonKey(name: 'is_rerun_requested') bool isRerunRequested,
    @JsonKey(name: 'artefact_build_id') required int artefactBuildId,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);
}

enum TestExecutionStatus {
  @JsonValue('FAILED')
  failed,
  @JsonValue('NOT_STARTED')
  notStarted,
  @JsonValue('NOT_TESTED')
  notTested,
  @JsonValue('IN_PROGRESS')
  inProgress,
  @JsonValue('PASSED')
  passed,
  @JsonValue('ENDED_PREMATURELY')
  endedPrematurely;

  bool get isCompleted {
    switch (this) {
      case notStarted:
      case inProgress:
      case notTested:
      case endedPrematurely:
        return false;
      case passed:
      case failed:
        return true;
    }
  }

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
      case endedPrematurely:
        return 'Ended Prematurely';
    }
  }

  Widget get icon {
    const size = 20.0;
    switch (this) {
      case notStarted:
        return const Tooltip(
          message: 'Not Started',
          child: Icon(YaruIcons.media_play, size: size),
        );
      case inProgress:
        return const Tooltip(
          message: 'In Progress',
          child: Icon(YaruIcons.refresh, size: size),
        );
      case passed:
        return Tooltip(
          message: 'Passed',
          child: Icon(
            YaruIcons.ok,
            color: YaruColors.light.success,
            size: size,
          ),
        );
      case failed:
        return const Tooltip(
          message: 'Failed',
          child: Icon(YaruIcons.error, color: YaruColors.red, size: size),
        );
      case notTested:
        return const Tooltip(
          message: 'Not Tested',
          child: Icon(YaruIcons.information, size: size),
        );
      case endedPrematurely:
        return const Tooltip(
          message: 'Ended Prematurely',
          child: Icon(YaruIcons.junk_filled, size: size),
        );
    }
  }
}
