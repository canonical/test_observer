// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';

import 'test_execution_relevant_link.dart';
import 'environment.dart';
import 'execution_metadata.dart';

part 'test_execution.freezed.dart';
part 'test_execution.g.dart';

@freezed
abstract class TestExecution with _$TestExecution {
  static const String reviewCommentJsonKey = 'review_comment';
  static const String reviewDecisionJsonKey = 'review_decision';
  static const String defaultTestPlanName = 'unknown';

  const factory TestExecution({
    required int id,
    @JsonKey(name: 'ci_link') required String? ciLink,
    @JsonKey(name: 'c3_link') required String? c3Link,
    required TestExecutionStatus status,
    required Environment environment,
    @Default(false) @JsonKey(name: 'is_rerun_requested') bool isRerunRequested,
    @JsonKey(name: 'artefact_build_id') int? artefactBuildId,
    @JsonKey(name: 'test_plan') required String testPlan,
    @Default([])
    @JsonKey(name: 'relevant_links')
    List<TestExecutionRelevantLink> relevantLinks,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @Default(ExecutionMetadata(data: {}))
    @JsonKey(name: 'execution_metadata')
    ExecutionMetadata executionMetadata,
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
