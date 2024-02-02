import 'package:dio/dio.dart';

import '../models/artefact.dart';

import '../models/artefact_build.dart';
import '../models/family_name.dart';
import '../models/test_execution.dart';
import '../models/test_result.dart';

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
}