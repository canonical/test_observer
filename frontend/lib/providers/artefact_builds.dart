// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/artefact_build.dart';
import '../models/test_execution.dart';
import 'api.dart';

part 'artefact_builds.g.dart';

@riverpod
class ArtefactBuilds extends _$ArtefactBuilds {
  @override
  Future<List<ArtefactBuild>> build(int artefactId) async {
    final api = ref.watch(apiProvider);
    return await api.getArtefactBuilds(artefactId);
  }

  Future<void> rerunTestExecutions(
    Set<int> testExecutionIds, {
    int? priority,
  }) async {
    final api = ref.read(apiProvider);
    await api.rerunTestExecutions(testExecutionIds, priority: priority);

    // Update all executions that share the same rerun group
    // (artefactBuildId, environment, testPlan) as the requested IDs,
    // since the backend deduplicates reruns by group rather than by
    // individual execution ID.
    final artefactBuilds = await future;
    final allExecutions = artefactBuilds.expand((ab) => ab.testExecutions);
    final requestedExecutions =
        allExecutions.where((te) => testExecutionIds.contains(te.id)).toList();
    final groups = {
      for (final te in requestedExecutions)
        (te.artefactBuildId, te.environment.id, te.testPlan),
    };

    await _updateTestExecutions(
      allExecutions
          .where(
            (te) => groups.contains(
              (te.artefactBuildId, te.environment.id, te.testPlan),
            ),
          )
          .map((te) => te.id)
          .toSet(),
      (te) => te.copyWith(isRerunRequested: true, rerunPriority: priority),
    );
  }

  Future<void> deleteRerunTestExecutions(Set<int> testExecutionIds) async {
    final api = ref.read(apiProvider);
    await api.deleteRerunForTestExecutions(testExecutionIds);

    final artefactBuilds = await future;
    final allExecutions = artefactBuilds.expand((ab) => ab.testExecutions);
    final requestedExecutions =
        allExecutions.where((te) => testExecutionIds.contains(te.id)).toList();
    final groups = {
      for (final te in requestedExecutions)
        (te.artefactBuildId, te.environment.id, te.testPlan),
    };

    await _updateTestExecutions(
      allExecutions
          .where(
            (te) => groups.contains(
              (te.artefactBuildId, te.environment.id, te.testPlan),
            ),
          )
          .map((te) => te.id)
          .toSet(),
      (te) => te.copyWith(isRerunRequested: false, rerunPriority: null),
    );
  }

  Future<void> _updateTestExecutions(
    Set<int> testExecutionIds,
    TestExecution Function(TestExecution) update,
  ) async {
    final artefactBuilds = await future;
    final newArtefactBuilds = <ArtefactBuild>[];
    for (final ab in artefactBuilds) {
      final newTestExecutions = [
        for (final te in ab.testExecutions)
          if (testExecutionIds.contains(te.id)) update(te) else te,
      ];

      newArtefactBuilds.add(ab.copyWith(testExecutions: newTestExecutions));
    }

    state = AsyncData(newArtefactBuilds);
  }
}
