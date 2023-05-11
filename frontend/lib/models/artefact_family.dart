import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
import 'stage.dart';

part 'artefact_family.freezed.dart';

@freezed
class ArtefactFamily with _$ArtefactFamily {
  const factory ArtefactFamily({
    required String name,
    @Default([]) List<Stage> stages,
  }) = _ArtefactFamily;
}
