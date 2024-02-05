import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'side_filters_visibility.g.dart';

@riverpod
class SideFiltersVisibility extends _$SideFiltersVisibility {
  @override
  bool build() {
    return false;
  }

  void set(bool value) {
    state = value;
  }
}
