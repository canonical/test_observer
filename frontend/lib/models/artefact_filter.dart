import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';

part 'artefact_filter.freezed.dart';

@freezed
class ArtefactFilter with _$ArtefactFilter {
  const factory ArtefactFilter({
    required String name,
    required Function(Artefact) retrieveArtefactOption,
    required List<({String name, bool value})> options,
  }) = _ArtefactFilter;
}
