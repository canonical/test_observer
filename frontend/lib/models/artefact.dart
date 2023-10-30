import 'package:freezed_annotation/freezed_annotation.dart';

import 'stage_name.dart';

part 'artefact.freezed.dart';
part 'artefact.g.dart';

@freezed
class Artefact with _$Artefact {
  const Artefact._();

  const factory Artefact({
    required int id,
    required String name,
    required String version,
    @Default(null) String? track,
    @Default(null) String? store,
    @Default(null) String? series,
    @Default(null) String? repo,
    required StageName stage,
  }) = _Artefact;

  factory Artefact.fromJson(Map<String, Object?> json) =>
      _$ArtefactFromJson(json);

  Map<String, String> get details => {
        'version': version,
        if (track != null) 'track': track!,
        if (store != null) 'store': store!,
        if (series != null) 'series': series!,
        if (repo != null) 'repo': repo!,
      };
}
