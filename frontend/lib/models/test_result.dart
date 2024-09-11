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

  Icon get icon {
    const size = 15.0;
    switch (this) {
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case skipped:
        return const Icon(
          YaruIcons.error,
          color: YaruColors.coolGrey,
          size: size,
        );
    }
  }
}
