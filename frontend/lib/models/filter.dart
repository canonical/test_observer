import 'package:freezed_annotation/freezed_annotation.dart';

part 'filter.freezed.dart';

@freezed
class Filter<T> with _$Filter<T> {
  const factory Filter({
    required String name,
    required Function(T) retrieveOption,
    required List<({String name, bool value})> options,
  }) = _Filter;
}
