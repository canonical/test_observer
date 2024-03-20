import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/family_name.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/artefact_builds.dart';
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

    final filters =
        container.read(pageFiltersProvider(Uri(path: AppRoutes.snaps))).filters;

    expect(filters[0].name, 'Assignee');
    expect(filters[0].detectedOptions, {dummyArtefact.assignee?.name});
    expect(filters[1].name, 'Status');
    expect(filters[1].detectedOptions, {dummyArtefact.status.name});
  });

  test('it extracts options from fetched test executions', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const artefactId = 1;

    // Wait on artefact builds to load cause test execution filters uses requireValue
    await container.read(artefactBuildsProvider(artefactId).future);

    final filters = container
        .read(pageFiltersProvider(Uri(path: '${AppRoutes.snaps}/$artefactId')))
        .filters;

    expect(filters[0].name, 'Review status');
    expect(filters[0].detectedOptions, {'Undecided'});
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
        testExecutions: [dummyTestExecution.copyWith(reviewDecision: [])],
      ),
    ];
  }
}
