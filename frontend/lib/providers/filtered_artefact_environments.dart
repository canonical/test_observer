// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
