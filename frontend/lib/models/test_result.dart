import 'package:freezed_annotation/freezed_annotation.dart';

part 'test_result.freezed.dart';
part 'test_result.g.dart';

@freezed
class TestResult with _$TestResult {
  const TestResult._();

  const factory TestResult({
    required String name,
    required TestResultStatus status,
    @Default('') String category,
    @Default('') String comment,
    @JsonKey(name: 'io_log') @Default('') String ioLog,
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
}
