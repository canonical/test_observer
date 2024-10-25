import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_environment.dart';
import '../models/filters.dart';
import '../routing.dart';
import 'artefact_environments.dart';

part 'filtered_artefact_environments.g.dart';

@riverpod
Future<List<ArtefactEnvironment>> filteredArtefactEnvironments(
  FilteredArtefactEnvironmentsRef ref,
  Uri pageUri,
) async {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final filters = emptyArtefactEnvironmentsFilters
      .copyWithQueryParams(pageUri.queryParametersAll);
  final searchValue =
      pageUri.queryParameters[CommonQueryParameters.searchQuery] ?? '';

  final environments =
      await ref.watch(artefactEnvironmentsProvider(artefactId).future);

  return environments
      .filter(
        (environment) =>
            filters.doesObjectPassFilters(environment) &&
            _passesSearch(environment, searchValue),
      )
      .toList();
}

bool _passesSearch(
  ArtefactEnvironment environment,
  String searchValue,
) {
  return environment.name.toLowerCase().contains(searchValue.toLowerCase());
}
