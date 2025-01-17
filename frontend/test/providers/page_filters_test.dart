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

import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/environment_review.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/artefact_environments.dart';
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

    // Wait on artefacts to load cause artefactFiltersProvider uses requireValue
    await container.read(familyArtefactsProvider(family).future);

    final pageFilters =
        container.read(pageFiltersProvider(Uri(path: AppRoutes.snaps)));

    expect(pageFilters.filters[0].name, 'Assignee');
    expect(
      pageFilters.filters[0].detectedOptions,
      {dummyArtefact.assignee.name},
    );
    expect(pageFilters.filters[1].name, 'Status');
    expect(
      pageFilters.filters[1].detectedOptions,
      {dummyArtefact.status.name},
    );
  });

  test('it extracts options from fetched test executions', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const artefactId = 1;

    // Wait on to load cause filters uses requireValue
    await container.read(artefactEnvironmentsProvider(artefactId).future);

    final pageFilters = container.read(
      pageFiltersProvider(Uri(path: '${AppRoutes.snaps}/$artefactId')),
    );

    expect(pageFilters.filters[0].name, 'Review status');
    expect(pageFilters.filters[0].detectedOptions, {'Undecided'});
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
