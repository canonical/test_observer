import 'package:freezed_annotation/freezed_annotation.dart';

part 'environment_issue.freezed.dart';
part 'environment_issue.g.dart';

@freezed
class EnvironmentIssue with _$EnvironmentIssue {
  const factory EnvironmentIssue({
    required int id,
    @JsonKey(name: 'environment_name') required String environmentName,
    required String description,
    required Uri? url,
    @JsonKey(name: 'is_confirmed') required bool isConfirmed,
  }) = _EnvironmentIssue;

  factory EnvironmentIssue.fromJson(Map<String, Object?> json) =>
      _$EnvironmentIssueFromJson(json);
}
