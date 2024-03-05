import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

part 'filter.freezed.dart';

@freezed
class Filter<T> with _$Filter<T> {
  const Filter._();

  const factory Filter({
    required String name,
    required String? Function(T) extractOption,
    required List<({String name, bool value})> options,
  }) = _Filter<T>;

  factory Filter.fromObjects({
    required String name,
    required String? Function(T) extractOption,
    required List<T> objects,
  }) {
    final names = <String>{};
    for (final artefact in objects) {
      final name = extractOption(artefact);
      if (name != null) names.add(name);
    }

    final options = [
      for (final name in names.toList().sorted()) (name: name, value: false),
    ];

    return Filter(name: name, extractOption: extractOption, options: options);
  }

  bool doesObjectPassFilter(T object) {
    final noOptionsSelected = options.none((option) => option.value);
    if (noOptionsSelected) return true;
    final selectedOptions = {
      for (final option in options)
        if (option.value) option.name,
    };
    return selectedOptions.contains(extractOption(object));
  }

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
