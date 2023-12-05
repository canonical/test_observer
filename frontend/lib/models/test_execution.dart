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
    @JsonKey(name: 'ci_link') required String? ciLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
    @JsonKey(name: 'review_status')
    required TestExecutionReviewStatus reviewStatus,
    @JsonKey(name: 'review_comment') required String? reviewComment,
  }) = _TestExecution;

  factory TestExecution.fromJson(Map<String, Object?> json) =>
      _$TestExecutionFromJson(json);
}

enum TestExecutionReviewStatus {
  @JsonValue('UNDECIDED')
  undecided,
  @JsonValue('APPROVED')
  accepted,
  @JsonValue('MARKED_AS_FAILED')
  markedAsFailed;

  String get name {
    switch (this) {
      case undecided:
        return 'Undecided';
      case accepted:
        return 'Approved';
      case markedAsFailed:
        return 'Marked as Failed';
    }
  }

  Chip get chip {
    switch (this) {
      case undecided:
        return const Chip(
          label: Text('Undecided'),
          backgroundColor: Color.fromARGB(255, 168, 166, 166),
          side: BorderSide.none,
        );
      case accepted:
        return const Chip(
          label: Text('Approved'),
          backgroundColor: Color.fromARGB(255, 157, 205, 165),
          side: BorderSide.none,
        );
      case markedAsFailed:
        return const Chip(
          label: Text('Marked as failed'),
          backgroundColor: Color.fromARGB(255, 218, 150, 166),
        );
    }
  }
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
  passed;

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
    }
  }

  Icon get icon {
    const size = 20.0;
    switch (this) {
      case notStarted:
        return const Icon(YaruIcons.media_play, size: size);
      case inProgress:
        return const Icon(YaruIcons.refresh, size: size);
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case notTested:
        return const Icon(YaruIcons.information, size: size);
    }
  }
}
