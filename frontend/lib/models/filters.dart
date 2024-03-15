import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
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

  Filters<T> copyWithQueryParams(Map<String, List<String>> queryParams) {
    final filterValues = queryParams.map(
      (filterName, filterValues) => MapEntry(
        filterName.urlDecode,
        filterValues.map((value) => value.urlDecode).toSet(),
      ),
    );

    final newFilters = filters.map((filter) {
      final values = filterValues[filter.name];
      if (values == null) return filter;
      return filter.copyWithOptionValues(values);
    });

    return copyWith(filters: newFilters.toList());
  }

  Map<String, List<String>> toQueryParams() {
    final queryParams = <String, List<String>>{};
    for (final filter in filters) {
      final selectedOptions =
          filter.options.filter((option) => option.value).toList();
      if (selectedOptions.isNotEmpty) {
        queryParams[filter.name.urlEncode] =
            selectedOptions.map((option) => option.name.urlEncode).toList();
      }
    }
    return queryParams;
  }
}

Filters<Artefact> getArtefactFilters(
  List<Artefact> artefactsToFillOptionsWith,
) {
  return Filters<Artefact>(
    filters: [
      Filter<Artefact>.fromObjects(
        name: 'Assignee',
        extractOption: (artefact) => artefact.assignee?.name,
        objects: artefactsToFillOptionsWith,
      ),
      Filter<Artefact>.fromObjects(
        name: 'Status',
        extractOption: (artefact) => artefact.status.name,
        objects: artefactsToFillOptionsWith,
      ),
    ],
  );
}
