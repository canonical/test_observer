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

import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment_review.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/enriched_test_executions.dart';
import 'package:testcase_dashboard/providers/family_artefacts.dart';
import 'package:testcase_dashboard/providers/page_filters.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/routing.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it collects options from fetched artefacts', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const family = FamilyName.snap;

    // Wait on artefacts to load because pageFiltersProvider uses .value
    await container.read(familyArtefactsProvider(family).future);

    final filters =
        container.read(pageFiltersProvider(Uri(path: AppRoutes.snaps)));

    expect(filters[0].name, 'Assignee');
    expect(
      filters[0].options,
      [(name: dummyArtefact.assignee.name, isSelected: false)],
    );
    expect(filters[1].name, 'Status');
    expect(
      filters[1].options,
      [(name: dummyArtefact.status.name, isSelected: false)],
    );
  });

  test('it extracts options from fetched test executions', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const artefactId = 1;

    // Wait on to load because pageFiltersProvider uses .value
    await container.read(enrichedTestExecutionsProvider(artefactId).future);

    final filters = container.read(
      pageFiltersProvider(Uri(path: '${AppRoutes.snaps}/$artefactId')),
    );

    expect(filters[0].name, 'Review status');
    expect(filters[0].options, [(name: 'Undecided', isSelected: false)]);
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    return {dummyArtefact.id: dummyArtefact};
  }

  @override
  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    return [
      dummyArtefactBuild.copyWith(
        testExecutions: [dummyTestExecution],
      ),
    ];
  }

  @override
  Future<List<EnvironmentReview>> getArtefactEnvironmentReviews(
    int artefactId,
  ) async {
    return [dummyEnvironmentReview];
  }
}
