import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'global_error_message.g.dart';

@riverpod
class GlobalErrorMessage extends _$GlobalErrorMessage {
  @override
  String build() {
    return '';
  }

  void set(String errorMessage) {
    state = errorMessage;
  }
}
