import 'package:freezed_annotation/freezed_annotation.dart';

part 'test_issue.freezed.dart';
part 'test_issue.g.dart';

@freezed
class TestIssue with _$TestIssue {
  const factory TestIssue({
    required int id,
    @JsonKey(name: 'template_id') required String templateId,
    @JsonKey(name: 'case_name') required String caseName,
    required String description,
    required String url,
  }) = _TestIssue;

  factory TestIssue.fromJson(Map<String, Object?> json) =>
      _$TestIssueFromJson(json);
}
