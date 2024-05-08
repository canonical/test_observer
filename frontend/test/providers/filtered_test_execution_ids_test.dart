import 'package:mocktail/mocktail.dart';
import 'package:test/test.dart';
import 'package:testcase_dashboard/models/artefact_build.dart';
import 'package:testcase_dashboard/models/test_execution.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/artefact_builds.dart';
import 'package:testcase_dashboard/providers/filtered_test_execution_ids.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';

import '../dummy_data.dart';
import '../utilities.dart';

void main() {
  test('it returns all test executions if no filter is set', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const artefactId = 1;

    // Wait on artefact builds to load cause test execution filters uses requireValue
    await container.read(artefactBuildsProvider(artefactId).future);

    final filteredTestExecutionIds =
        container.read(filteredTestExecutionIdsProvider(Uri()));
    final builds = await apiMock.getArtefactBuilds(artefactId);
    final allTestExecutionIds = {
      for (final build in builds)
        for (final testExecution in build.testExecutions) testExecution.id,
    };

    expect(filteredTestExecutionIds, allTestExecutionIds);
  });

  test('it filters test executions by review status', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const artefactId = 1;

    // Wait on artefact builds to load cause test execution filters uses requireValue
    await container.read(artefactBuildsProvider(artefactId).future);

    final filteredTestExecutionIds = container.read(
      filteredTestExecutionIdsProvider(
        Uri(
          queryParameters: {
            'Review status': 'Undecided',
          },
        ),
      ),
    );

    expect(filteredTestExecutionIds, {1});
  });

  test('it filters test executions by test execution status', () async {
    final apiMock = ApiRepositoryMock();
    final container = createContainer(
      overrides: [apiProvider.overrideWith((ref) => apiMock)],
    );
    const artefactId = 1;

    // Wait on artefact builds to load cause test execution filters uses requireValue
    await container.read(artefactBuildsProvider(artefactId).future);

    final filteredTestExecutionIds = container.read(
      filteredTestExecutionIdsProvider(
        Uri(
          queryParameters: {
            'Execution status': 'Failed',
          },
        ),
      ),
    );

    expect(filteredTestExecutionIds, {1});
  });
}

class ApiRepositoryMock extends Mock implements ApiRepository {
  @override
  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    return [
      dummyArtefactBuild.copyWith(
        testExecutions: [
          dummyTestExecution.copyWith(
            id: 1,
            reviewDecision: [],
            status: TestExecutionStatus.failed,
          ),
          dummyTestExecution.copyWith(
            id: 2,
            reviewDecision: [
              TestExecutionReviewDecision.approvedAllTestsPass,
            ],
            status: TestExecutionStatus.passed,
          ),
        ],
      ),
    ];
  }
}
