import 'package:freezed_annotation/freezed_annotation.dart';

part 'filter.freezed.dart';

@freezed
class Filter<T> with _$Filter<T> {
  const Filter._();

  const factory Filter({
    required String name,
    required String? Function(T) extractOption,
    @Default(<String>{}) Set<String> selectedOptions,
    @Default(<String>[]) List<String> availableOptions,
  }) = _Filter<T>;

  bool doesObjectPassFilter(T object) {
    return selectedOptions.isEmpty ||
        selectedOptions.contains(extractOption(object));
  }
}
