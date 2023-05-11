import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';

part 'stage.freezed.dart';

@freezed
class Stage with _$Stage {
  const factory Stage({
    required String name,
    @Default([]) List<Artefact> artefacts,
  }) = _Stage;
}
