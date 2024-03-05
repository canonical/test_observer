import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'filter.dart';

part 'filters.freezed.dart';

@freezed
class Filters<T> with _$Filters<T> {
  const Filters._();

  const factory Filters({
    required List<Filter<T>> filters,
  }) = _Filters<T>;

  Filters<T> copyWithFilterOptionValue(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    return copyWith(
      filters: [
        for (final filter in filters)
          if (filter.name == filterName)
            filter.copyWithOptionValue(optionName, optionValue)
          else
            filter,
      ],
    );
  }

  bool doesObjectPassFilters(T object) =>
      filters.all((filter) => filter.doesObjectPassFilter(object));
}
