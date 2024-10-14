import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'artefact.dart';
import 'environment_review.dart';
import 'filter.dart';
import 'test_execution.dart';

part 'filters.freezed.dart';

@freezed
class FiltersGroup<T> with _$FiltersGroup<T> {
  const FiltersGroup._();

  const factory FiltersGroup({
    required List<Filter<T>> filters,
  }) = _Filters<T>;

  FiltersGroup<T> copyWithFilterOptionValue(
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

  FiltersGroup<T> copyWithQueryParams(Map<String, List<String>> queryParams) {
    final newFilters = filters.map((filter) {
      final values = queryParams[filter.name]?.toSet();
      if (values == null || values.isEmpty) return filter;
      return filter.copyWith(
        selectedOptions: values.toSet(),
        detectedOptions: filter.detectedOptions.toSet().union(values).toList()
          ..sort(),
      );
    });

    return copyWith(filters: newFilters.toList());
  }

  Map<String, List<String>> toQueryParams() {
    final queryParams = <String, List<String>>{};
    for (final filter in filters) {
      if (filter.selectedOptions.isNotEmpty) {
        queryParams[filter.name] = filter.selectedOptions.toList();
      }
    }
    return queryParams;
  }

  FiltersGroup<T> copyWithOptionsExtracted(List<T> objects) {
    final newFilters = <Filter<T>>[];
    for (final filter in filters) {
      final options = <String>{};
      for (final object in objects) {
        final option = filter.extractOption(object);
        if (option != null) options.add(option);
      }
      newFilters
          .add(filter.copyWith(detectedOptions: options.toList()..sort()));
    }
    return copyWith(filters: newFilters);
  }
}

final emptyArtefactFilters = FiltersGroup<Artefact>(
  filters: [
    Filter<Artefact>(
      name: 'Assignee',
      extractOption: (artefact) => artefact.assignee?.name,
    ),
    Filter<Artefact>(
      name: 'Status',
      extractOption: (artefact) => artefact.status.name,
    ),
    Filter<Artefact>(
      name: 'Due date',
      extractOption: (artefact) {
        final now = DateTime.now();
        final dueDate = artefact.dueDate;

        if (dueDate == null) return 'No due date';
        if (dueDate.isBefore(now)) return 'Overdue';

        final daysDueIn = now.difference(dueDate).inDays;
        if (daysDueIn >= 7) return 'More than a week';
        return 'Within a week';
      },
    ),
  ],
);

final emptyTestExecutionFilters = FiltersGroup<TestExecution>(
  filters: [
    Filter<TestExecution>(
      name: 'Execution status',
      extractOption: (te) => te.status.name,
    ),
  ],
);

final emptyEnvironmentReviewFilters = FiltersGroup<EnvironmentReview>(
  filters: [
    Filter<EnvironmentReview>(
      name: 'Review status',
      extractOption: (te) =>
          te.reviewDecision.isEmpty ? 'Undecided' : 'Reviewed',
    ),
  ],
);
