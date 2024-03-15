import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
import 'filter.dart';
import 'test_execution.dart';

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
            if (optionValue)
              filter.copyWith(
                selectedOptions: filter.selectedOptions.union({optionName}),
              )
            else
              filter.copyWith(
                selectedOptions:
                    filter.selectedOptions.difference({optionName}),
              )
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
      return filter.copyWith(selectedOptions: values);
    });

    return copyWith(filters: newFilters.toList());
  }

  Map<String, List<String>> toQueryParams() {
    final queryParams = <String, List<String>>{};
    for (final filter in filters) {
      if (filter.selectedOptions.isNotEmpty) {
        queryParams[filter.name.urlEncode] =
            filter.selectedOptions.map((option) => option.urlEncode).toList();
      }
    }
    return queryParams;
  }

  Filters<T> copyWithOptionsExtracted(List<T> objects) {
    final newFilters = <Filter<T>>[];
    for (final filter in filters) {
      final options = <String>{};
      for (final object in objects) {
        final option = filter.extractOption(object);
        if (option != null) options.add(option);
      }
      newFilters
          .add(filter.copyWith(availableOptions: options.toList()..sort()));
    }
    return copyWith(filters: newFilters);
  }
}

final emptyArtefactFilters = Filters<Artefact>(
  filters: [
    Filter<Artefact>(
      name: 'Assignee',
      extractOption: (artefact) => artefact.assignee?.name,
    ),
    Filter<Artefact>(
      name: 'Status',
      extractOption: (artefact) => artefact.status.name,
    ),
  ],
);

final emptyTestExecutionFilters = Filters<TestExecution>(
  filters: [
    Filter<TestExecution>(
      name: 'Review status',
      extractOption: (te) =>
          te.reviewDecision.isEmpty ? 'Undecided' : 'Reviewed',
    ),
    Filter<TestExecution>(
      name: 'Execution status',
      extractOption: (te) => te.status.name,
    ),
  ],
);
