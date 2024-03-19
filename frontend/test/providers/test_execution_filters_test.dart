import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/artefact_builds.dart';
import 'package:testcase_dashboard/providers/test_execution_filters.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it extracts options from fetched test executions', () async {
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => ApiRepositoryMock())],
    );
    const artefactId = 1;

    // Wait on artefact builds to load cause test execution filters uses requireValue
    await container.read(artefactBuildsProvider(artefactId).future);

    final filters =
        container.read(testExecutionFiltersProvider(artefactId, Uri())).filters;

    expect(filters[0].name, 'Review status');
    expect(filters[0].detectedOptions, {'Undecided'});
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    return [
      dummyArtefactBuild.copyWith(
        testExecutions: [dummyTestExecution.copyWith(reviewDecision: [])],
      ),
    ];
  }
}
