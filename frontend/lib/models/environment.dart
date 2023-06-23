import 'package:freezed_annotation/freezed_annotation.dart';

part 'environment.freezed.dart';
part 'environment.g.dart';

@freezed
class Environment with _$Environment {
  const factory Environment({
    required int id,
    required String name,
    required String architecture,
  }) = _Environment;

  factory Environment.fromJson(Map<String, Object?> json) =>
      _$EnvironmentFromJson(json);
}
