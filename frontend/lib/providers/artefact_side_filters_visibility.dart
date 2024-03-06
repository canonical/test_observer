import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'artefact_side_filters_visibility.g.dart';

@riverpod
class ArtefactSideFiltersVisibility extends _$ArtefactSideFiltersVisibility {
  @override
  bool build() {
    return false;
  }

  void set(bool value) {
    state = value;
  }
}
