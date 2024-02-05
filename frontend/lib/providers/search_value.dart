import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'search_value.g.dart';

@riverpod
class SearchValue extends _$SearchValue {
  @override
  String build() {
    return '';
  }

  void onChanged(String newValue) {
    state = newValue;
  }
}
