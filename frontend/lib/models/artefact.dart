import 'package:freezed_annotation/freezed_annotation.dart';

part 'artefact.freezed.dart';

@freezed
class Artefact with _$Artefact {
  const factory Artefact({
    required String name,
  }) = _Artefact;
}

const dummyArtefact = Artefact(name: 'Artefact');
