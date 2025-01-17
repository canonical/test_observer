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

part 'test_result.freezed.dart';
part 'test_result.g.dart';

@freezed
class PreviousTestResult with _$PreviousTestResult {
  const PreviousTestResult._();

  const factory PreviousTestResult({
    required TestResultStatus status,
    required String version,
    @JsonKey(name: 'artefact_id') required int artefactId,
  }) = _PreviousTestResult;

  factory PreviousTestResult.fromJson(Map<String, Object?> json) =>
      _$PreviousTestResultFromJson(json);
}

@freezed
class TestResult with _$TestResult {
  const TestResult._();

  const factory TestResult({
    required String name,
    required TestResultStatus status,
    @Default('') String category,
    @Default('') String comment,
    @JsonKey(name: 'template_id') @Default('') String templateId,
    @JsonKey(name: 'io_log') @Default('') String ioLog,
    @JsonKey(name: 'previous_results')
    @Default([])
    List<PreviousTestResult> previousResults,
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
