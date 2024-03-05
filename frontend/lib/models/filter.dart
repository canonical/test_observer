import 'package:freezed_annotation/freezed_annotation.dart';

part 'filter.freezed.dart';

@freezed
class Filter<T> with _$Filter<T> {
  const Filter._();

  const factory Filter({
    required String name,
    required String? Function(T) retrieveOption,
    required List<({String name, bool value})> options,
  }) = _Filter<T>;

  Filter<T> copyWithOptionValue(String optionName, bool optionValue) {
    return copyWith(
      options: [
        for (final option in options)
          if (option.name == optionName)
            (name: optionName, value: optionValue)
          else
            option,
      ],
    );
  }
}
