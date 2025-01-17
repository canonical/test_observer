// Copyright (C) 2024 Canonical Ltd.
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

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/filters.dart';
import '../routing.dart';
import 'artefact_environments.dart';
import 'family_artefacts.dart';

part 'page_filters.g.dart';

@riverpod
class PageFilters extends _$PageFilters {
  @override
  Filters build(Uri pageUri) {
    if (AppRoutes.isDashboardPage(pageUri)) {
      final family = AppRoutes.familyFromUri(pageUri);
      final artefacts = ref
          .watch(familyArtefactsProvider(family))
          .requireValue
          .values
          .toList();

      return createEmptyArtefactFilters(family)
          .copyWithOptionsExtracted(artefacts)
          .copyWithQueryParams(pageUri.queryParametersAll);
    }

    if (AppRoutes.isArtefactPage(pageUri)) {
      final artefactId = AppRoutes.artefactIdFromUri(pageUri);
      final artefactEnvironments =
          ref.watch(artefactEnvironmentsProvider(artefactId)).requireValue;

      return emptyArtefactEnvironmentsFilters
          .copyWithOptionsExtracted(artefactEnvironments)
          .copyWithQueryParams(pageUri.queryParametersAll);
    }

    throw Exception('Called pageFiltersProvider in unknown page $pageUri');
  }

  void handleFilterOptionChange(
    String filterName,
    String optionName,
    bool optionValue,
  ) {
    state = state.copyWithFilterOptionValue(
      filterName,
      optionName,
      optionValue,
    );
  }
}
