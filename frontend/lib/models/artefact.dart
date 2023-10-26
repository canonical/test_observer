import 'package:freezed_annotation/freezed_annotation.dart';

import 'stage_name.dart';

part 'artefact.freezed.dart';
part 'artefact.g.dart';

@freezed
class Artefact with _$Artefact {
  const factory Artefact({
    required int id,
    required String name,
    required String version,
    required Map<String, dynamic> source,
    required StageName stage,
  }) = _Artefact;

  factory Artefact.fromJson(Map<String, Object?> json) =>
      _$ArtefactFromJson(json);
}
