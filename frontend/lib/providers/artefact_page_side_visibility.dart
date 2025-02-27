import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'artefact_page_side_visibility.g.dart';

@riverpod
class ArtefactPageSideVisibility extends _$ArtefactPageSideVisibility {
  @override
  bool build() {
    return true;
  }

  void set(bool value) {
    state = value;
  }
}
