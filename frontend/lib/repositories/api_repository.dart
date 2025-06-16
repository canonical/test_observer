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

import 'package:dio/dio.dart';

import '../models/artefact.dart';

import '../models/artefact_build.dart';
import '../models/artefact_version.dart';
import '../models/environment_issue.dart';
import '../models/environment_review.dart';
import '../models/family_name.dart';
import '../models/rerun_request.dart';
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

  Future<Artefact> changeArtefactComment(
    int artefactId,
    String comment,
  ) async {
    final response = await dio
        .patch('/v1/artefacts/$artefactId', data: {'comment': comment});
    return Artefact.fromJson(response.data);
  }

  Future<List<ArtefactBuild>> getArtefactBuilds(int artefactId) async {
    final response = await dio.get('/v1/artefacts/$artefactId/builds');
    final List artefactBuildsJson = response.data;
    final artefactBuilds =
        artefactBuildsJson.map((json) => ArtefactBuild.fromJson(json)).toList();
    return artefactBuilds;
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

  Future<Artefact> getArtefact(int artefactId) async {
    final response = await dio.get('/v1/artefacts/$artefactId');
    return Artefact.fromJson(response.data);
  }

  Future<List<ArtefactVersion>> getArtefactVersions(
    int artefactId,
  ) async {
    final response = await dio.get('/v1/artefacts/$artefactId/versions');
    final List data = response.data;
    return data.map((json) => ArtefactVersion.fromJson(json)).toList();
  }

  Future<List<EnvironmentIssue>> getEnvironmentsIssues() async {
    final response = await dio.get('/v1/environments/reported-issues');
    final List issuesJson = response.data;
    return issuesJson.map((json) => EnvironmentIssue.fromJson(json)).toList();
  }

  Future<EnvironmentIssue> createEnvironmentIssue(
    String url,
    String description,
    String environmentName,
    bool isConfirmed,
  ) async {
    final response = await dio.post(
      '/v1/environments/reported-issues',
      data: {
        'url': url.isEmpty ? null : url,
        'description': description,
        'environment_name': environmentName,
        'is_confirmed': isConfirmed,
      },
    );
    return EnvironmentIssue.fromJson(response.data);
  }

  Future<EnvironmentIssue> updateEnvironmentIssue(
    EnvironmentIssue issue,
  ) async {
    final response = await dio.put(
      '/v1/environments/reported-issues/${issue.id}',
      data: issue.toJson(),
    );
    return EnvironmentIssue.fromJson(response.data);
  }

  Future<void> deleteEnvironmentIssue(int issueId) async {
    await dio.delete('/v1/environments/reported-issues/$issueId');
  }

  Future<List<EnvironmentReview>> getArtefactEnvironmentReviews(
    int artefactId,
  ) async {
    final response =
        await dio.get('/v1/artefacts/$artefactId/environment-reviews');
    final List environmentReviewsJson = response.data;
    return environmentReviewsJson
        .map((json) => EnvironmentReview.fromJson(json))
        .toList();
  }

  Future<EnvironmentReview> updateEnvironmentReview(
    int artefactId,
    EnvironmentReview review,
  ) async {
    final response = await dio.patch(
      '/v1/artefacts/$artefactId/environment-reviews/${review.id}',
      data: review.toJson(),
    );
    return EnvironmentReview.fromJson(response.data);
  }


  Future<List<dynamic>> getKnownIssuesReport({
    String? templateId,
    String? caseName,
  }) async {
    final queryParameters = <String, String>{};
    if (templateId != null) {
      queryParameters['template_id'] = templateId;
    }
    if (caseName != null) {
      queryParameters['case_name'] = caseName;
    }
    
    final response = await dio.get(
      '/v1/test-cases/reported-issues',
      queryParameters: queryParameters,
    );
    return response.data;
  }

  Future<String> getTestResultsCsv({
    DateTime? startDate,
    DateTime? endDate,
  }) async {
    final queryParameters = <String, String>{};
    if (startDate != null) {
      queryParameters['start_date'] = startDate.toIso8601String();
    }
    if (endDate != null) {
      queryParameters['end_date'] = endDate.toIso8601String();
    }
    
    final response = await dio.get(
      '/v1/reports/test-results',
      queryParameters: queryParameters,
    );
    return response.data;
  }

  Future<Map<String, dynamic>> getTestSummaryReport({
    DateTime? startDate,
    DateTime? endDate,
    List<String>? families,
  }) async {
    final queryParameters = <String, String>{};
    if (startDate != null) {
      queryParameters['start_date'] = startDate.toIso8601String();
    }
    if (endDate != null) {
      queryParameters['end_date'] = endDate.toIso8601String();
    }
    if (families != null && families.isNotEmpty) {
      for (final family in families) {
        queryParameters.addAll({'families': family});
      }
    }
    
    final response = await dio.get(
      '/v1/reports/test-summary',
      queryParameters: queryParameters,
    );
    return response.data;
  }

  Future<Map<String, bool>> batchCheckTestCaseIssues(
    List<String> testIdentifiers,
  ) async {
    final response = await dio.post(
      '/v1/reports/test-summary/batch-issues-check',
      data: {'test_identifiers': testIdentifiers},
    );
    return Map<String, bool>.from(response.data);
  }
}
