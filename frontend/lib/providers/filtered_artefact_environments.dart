// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_environment.dart';
import 'filtered_enriched_test_executions.dart';

part 'filtered_artefact_environments.g.dart';

@riverpod
Future<List<ArtefactEnvironment>> filteredArtefactEnvironments(
  Ref ref,
  Uri pageUri,
) async {
  final enrichedExecutions =
      await ref.watch(filteredEnrichedTestExecutionsProvider(pageUri).future);
  final groupedEnrichedExecutions =
      enrichedExecutions.groupBy((ee) => ee.environmentReview);
  return groupedEnrichedExecutions
      .mapEntries(
        (entry) => ArtefactEnvironment(
          review: entry.key,
          runsDescending: entry.value
              .map((ee) => ee.testExecution)
              .sortedByDescending((te) => te.id),
        ),
      )
      .toList();
}
