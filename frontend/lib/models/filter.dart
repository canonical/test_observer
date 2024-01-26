import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';

part 'filter.freezed.dart';

@freezed
class Filter with _$Filter {
  const factory Filter({
    required String name,
    required Function(Artefact) retrieveArtefactOption,
    required List<({String name, bool value})> options,
  }) = _Filter;
}
