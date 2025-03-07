import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../filtering/enriched_test_execution_filters.dart';
import '../routing.dart';
import 'enriched_test_executions.dart';

part 'filters_state.g.dart';

typedef FilterState = ({
  String name,
  List<({String name, bool isSelected})> options
});

@riverpod
class FiltersState extends _$FiltersState {
  @override
  Future<List<FilterState>> build(Uri pageUri) async {
    final result = <FilterState>[];
    final artefactId = AppRoutes.artefactIdFromUri(pageUri);
    final queryParams = pageUri.queryParametersAll;
    final enrichedExecutions =
        await ref.watch(enrichedTestExecutionsProvider(artefactId).future);

    for (var filter in enrichedTestExecutionFilters) {
      final selectedOptions = (queryParams[filter.name] ?? []).toSet();
      final allOptions = filter.extractOptions(enrichedExecutions);
      result.add(
        (
          name: filter.name,
          options: allOptions
              .map(
                (option) => (
                  name: option,
                  isSelected: selectedOptions.contains(option),
                ),
              )
              .toList()
        ),
      );
    }

    return result;
  }

  Future<void> onChanged(
    String filterName,
    String optionName,
    bool isSelected,
  ) async {
    final filters = await future;
    state = AsyncData(
      filters.map((filter) {
        if (filter.name != filterName) {
          return filter;
        }
        return (
          name: filterName,
          options: filter.options
              .map(
                (option) => (
                  name: option.name,
                  isSelected:
                      option.name == optionName ? isSelected : option.isSelected
                ),
              )
              .toList(),
        );
      }).toList(),
    );
  }

  static Map<String, List<String>> toQueryParams(List<FilterState> filters) {
    return {
      for (var filter in filters)
        filter.name: filter.options
            .filter((option) => option.isSelected)
            .map((option) => option.name)
            .toList(),
    };
  }
}
