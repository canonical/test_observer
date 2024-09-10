import 'package:freezed_annotation/freezed_annotation.dart';

part 'artefact_version.freezed.dart';
part 'artefact_version.g.dart';

@freezed
class ArtefactVersion with _$ArtefactVersion {
  const factory ArtefactVersion({
    @JsonKey(name: 'artefact_id') required int artefactId,
    required String version,
  }) = _ArtefactVersion;

  factory ArtefactVersion.fromJson(Map<String, Object?> json) =>
      _$ArtefactVersionFromJson(json);
}
