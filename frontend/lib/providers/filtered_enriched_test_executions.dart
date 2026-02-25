// Copyright 2025 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../filtering/enriched_test_execution_filters.dart';
import '../models/enriched_test_execution.dart';
import '../routing.dart';
import 'enriched_test_executions.dart';

part 'filtered_enriched_test_executions.g.dart';

@riverpod
Future<List<EnrichedTestExecution>> filteredEnrichedTestExecutions(
  Ref ref,
  Uri pageUri,
) async {
  final artefactId = AppRoutes.artefactIdFromUri(pageUri);
  final searchValue =
      pageUri.queryParameters[CommonQueryParameters.searchQuery] ?? '';
  final parameters = pageUri.queryParametersAll;

  List<EnrichedTestExecution> result =
      await ref.watch(enrichedTestExecutionsProvider(artefactId).future);

  for (var filter in enrichedTestExecutionFilters) {
    final filterOptions = parameters[filter.name];
    if (filterOptions != null) {
      result = filter.filter(result, filterOptions.toSet());
    }
  }

  result = result
      .filter(
        (ee) => ee.testExecution.environment.name
            .toLowerCase()
            .contains(searchValue.toLowerCase()),
      )
      .toList();

  return result;
}
