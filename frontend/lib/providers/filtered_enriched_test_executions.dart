import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../filtering/enriched_test_execution_filters.dart';
import '../models/enriched_test_execution.dart';
import '../routing.dart';
import 'enriched_test_executions.dart';

part 'filtered_enriched_test_executions.g.dart';

@riverpod
Future<List<EnrichedTestExecution>> filteredEnrichedTestExecutions(
  FilteredEnrichedTestExecutionsRef ref,
  Uri pageUri,
) async {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  List<EnrichedTestExecution> result =
      await ref.watch(enrichedTestExecutionsProvider(artefactId).future);

  final parameters = pageUri.queryParametersAll;
  for (var filter in enrichedTestExecutionFilters) {
    final filterOptions = parameters[filter.name];
    if (filterOptions != null) {
      result = filter.filter(result, filterOptions.toSet());
    }
  }

  return result;
}
