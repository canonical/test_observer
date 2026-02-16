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

import 'issue_attachment.dart';

part 'test_result.freezed.dart';
part 'test_result.g.dart';

@freezed
abstract class PreviousTestResult with _$PreviousTestResult {
  const PreviousTestResult._();

  const factory PreviousTestResult({
    required TestResultStatus status,
    required String version,
    @JsonKey(name: 'artefact_id') required int artefactId,
    @JsonKey(name: 'test_execution_id') required int testExecutionId,
    @JsonKey(name: 'test_result_id') required int testResultId,
  }) = _PreviousTestResult;

  factory PreviousTestResult.fromJson(Map<String, Object?> json) =>
      _$PreviousTestResultFromJson(json);
}

@freezed
abstract class TestResult with _$TestResult {
  const TestResult._();

  const factory TestResult({
    required int id,
    required String name,
    required TestResultStatus status,
    @JsonKey(name: 'created_at') required DateTime createdAt,
    @Default('') String category,
    @Default('') String comment,
    @JsonKey(name: 'template_id') @Default('') String templateId,
    @JsonKey(name: 'io_log') @Default('') String ioLog,
    @JsonKey(name: 'previous_results')
    @Default([])
    List<PreviousTestResult> previousResults,
    @JsonKey(name: 'issues')
    @Default([])
    List<IssueAttachment> issueAttachments,
  }) = _TestResult;

  factory TestResult.fromJson(Map<String, Object?> json) =>
      _$TestResultFromJson(json);
}

enum TestResultStatus {
  @JsonValue('FAILED')
  failed,
  @JsonValue('PASSED')
  passed,
  @JsonValue('SKIPPED')
  skipped;

  static TestResultStatus fromString(String value) {
    return TestResultStatus.values.firstWhere(
      (status) => status.name.toUpperCase() == value.toUpperCase(),
      orElse: () => throw ArgumentError('Invalid TestResultStatus: $value'),
    );
  }

  String get name {
    switch (this) {
      case failed:
        return 'Failed';
      case passed:
        return 'Passed';
      case skipped:
        return 'Skipped';
    }
  }

  String get apiValue {
    switch (this) {
      case passed:
        return 'PASSED';
      case failed:
        return 'FAILED';
      case skipped:
        return 'SKIPPED';
    }
  }

  Icon getIcon({double scale = 1}) {
    final size = 15.0 * scale;
    switch (this) {
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case skipped:
        return Icon(
          YaruIcons.error,
          color: YaruColors.coolGrey,
          size: size,
        );
    }
  }
}
