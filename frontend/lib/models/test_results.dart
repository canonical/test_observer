import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_icons/yaru_icons.dart';

part 'test_results.freezed.dart';
part 'test_results.g.dart';

@freezed
class TestResult with _$TestResult {
  const factory TestResult({
    required int id,
    required String name,
    required String type,
    required TestResultStatus status,
    required String io_log,
    required String comments,
  }) = _TestResult;

  factory TestResult.fromJson(Map<String, Object?> json) =>
      _$TestResultFromJson(json);

}

enum TestResultStatus {
  @JsonValue('fail')
  failed,
  @JsonValue('pass')
  passed,
  @JsonValue('skip')
  skipped;

  String get name {
    switch (this) {
      case passed:
        return 'Passed';
      case failed:
        return 'Failed';
      case skipped:
        return 'Skipped';
    }
  }

  Icon get icon {
    const size = 20.0;
    switch (this) {
      case passed:
        return Icon(YaruIcons.ok, color: YaruColors.light.success, size: size);
      case failed:
        return const Icon(YaruIcons.error, color: YaruColors.red, size: size);
      case skipped:
        return const Icon(YaruIcons.question, size: size);
    }
  }
}