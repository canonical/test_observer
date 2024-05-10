import 'package:freezed_annotation/freezed_annotation.dart';

part 'rerun_request.freezed.dart';
part 'rerun_request.g.dart';

@freezed
class RerunRequest with _$RerunRequest {
  const factory RerunRequest({
    @JsonKey(name: 'test_execution_id') required int testExecutionId,
    @JsonKey(name: 'ci_link') required String ciLink,
  }) = _RerunRequest;

  factory RerunRequest.fromJson(Map<String, Object?> json) =>
      _$RerunRequestFromJson(json);
}
