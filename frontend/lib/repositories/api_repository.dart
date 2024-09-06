import 'package:dio/dio.dart';

import '../models/artefact.dart';

import '../models/artefact_build.dart';
import '../models/family_name.dart';
import '../models/rerun_request.dart';
import '../models/test_execution.dart';
import '../models/test_issue.dart';
import '../models/test_result.dart';
import '../models/test_event.dart';

class ApiRepository {
  final Dio dio;

  const ApiRepository({required this.dio});

  Future<Map<int, Artefact>> getFamilyArtefacts(FamilyName family) async {
    final response = await dio
        .get('/v1/artefacts', queryParameters: {'family': family.name});
    final artefacts = {
      for (final json in response.data)
        json['id'] as int: Artefact.fromJson(json),
    };
    return artefacts;
  }

  Future<Artefact> changeArtefactStatus(
    int artefactId,
    ArtefactStatus newStatus,
  ) async {
    final response = await dio.patch(
      '/v1/artefacts/$artefactId',
      data: {'status': newStatus.toJson()},
    );
    return Artefact.fromJson(response.data);
  }

  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    final response = await dio.get('/v1/artefacts/$artefactId/builds');
    final List artefactBuildsJson = response.data;
    final artefactBuilds =
        artefactBuildsJson.map((json) => ArtefactBuild.fromJson(json)).toList();
    return artefactBuilds;
  }

  Future<TestExecution> changeTestExecutionReview(
    int testExecutionId,
    List<TestExecutionReviewDecision> reviewDecision,
    String reviewComment,
  ) async {
    final response = await dio.patch(
      '/v1/test-executions/$testExecutionId',
      data: TestExecution.updateReviewDecisionRequestData(
        reviewComment,
        reviewDecision,
      ),
    );
    return TestExecution.fromJson(response.data);
  }

  Future<List<TestResult>> getTestExecutionResults(int testExecutionId) async {
    final response =
        await dio.get('/v1/test-executions/$testExecutionId/test-results');
    final List testResultsJson = response.data;
    final testResults =
        testResultsJson.map((json) => TestResult.fromJson(json)).toList();
    return testResults;
  }

  Future<List<TestEvent>> getTestExecutionEvents(int testExecutionId) async {
    final response =
        await dio.get('/v1/test-executions/$testExecutionId/status_update');
    final List testEventsJson = response.data;
    final testEvents =
        testEventsJson.map((json) => TestEvent.fromJson(json)).toList();
    return testEvents;
  }

  Future<List<RerunRequest>> rerunTestExecutions(
    Set<int> testExecutionIds,
  ) async {
    final response = await dio.post(
      '/v1/test-executions/reruns',
      data: {'test_execution_ids': testExecutionIds.toList()},
    );
    final List rerunsJson = response.data;
    final reruns =
        rerunsJson.map((json) => RerunRequest.fromJson(json)).toList();
    return reruns;
  }

  Future<List<TestIssue>> getTestIssues() async {
    final response = await dio.get('/v1/test-cases/reported-issues');
    final List issuesJson = response.data;
    return issuesJson.map((json) => TestIssue.fromJson(json)).toList();
  }

  Future<TestIssue> updateTestIssue(TestIssue issue) async {
    final response = await dio.put(
      '/v1/test-cases/reported-issues/${issue.id}',
      data: issue.toJson(),
    );
    return TestIssue.fromJson(response.data);
  }

  Future<TestIssue> createTestIssue(
    String url,
    String description,
    String? caseName,
    String? templateId,
  ) async {
    final response = await dio.post(
      '/v1/test-cases/reported-issues',
      data: {
        'url': url,
        'description': description,
        if (caseName != null) 'case_name': caseName,
        if (templateId != null) 'template_id': templateId,
      },
    );
    return TestIssue.fromJson(response.data);
  }

  Future<void> deleteTestIssue(int issueId) async {
    await dio.delete('/v1/test-cases/reported-issues/$issueId');
  }
}
