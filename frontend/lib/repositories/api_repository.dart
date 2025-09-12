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
import '../models/execution_metadata.dart';
import '../models/issue.dart';
import '../models/artefact_build.dart';
import '../models/artefact_version.dart';
import '../models/detailed_test_results.dart';
import '../models/environment_issue.dart';
import '../models/environment_review.dart';
import '../models/family_name.dart';
import '../models/rerun_request.dart';
import '../models/test_issue.dart';
import '../models/test_result.dart';
import '../models/test_event.dart';
import '../models/user.dart';

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

  Future<List<String>> getEnvironments() async {
    final response = await dio.get('/v1/environments');
    final Map<String, dynamic> data = response.data;
    final List<dynamic> environments = data['environments'] ?? [];
    return environments.cast<String>();
  }

  Future<List<String>> getTestCases() async {
    final response = await dio.get('/v1/test-cases');
    final Map<String, dynamic> data = response.data;
    final List<dynamic> testCasesData = data['test_cases'] ?? [];
    return testCasesData.map((item) => item['test_case'] as String).toList();
  }

  Future<TestResultsSearchResult> searchTestResults({
    List<String>? families,
    List<String>? environments,
    List<String>? testCases,
    List<String>? templateIds,
    ExecutionMetadata? executionMetadata,
    List<int>? issues,
    DateTime? fromDate,
    DateTime? untilDate,
    int? limit,
    int? offset,
  }) async {
    final queryParams = <String, dynamic>{};

    if (families != null && families.isNotEmpty) {
      queryParams['families'] = families;
    }

    if (environments != null && environments.isNotEmpty) {
      queryParams['environments'] = environments;
    }

    if (testCases != null && testCases.isNotEmpty) {
      queryParams['test_cases'] = testCases;
    }

    if (templateIds != null && templateIds.isNotEmpty) {
      queryParams['template_ids'] = templateIds;
    }

    if (executionMetadata != null && executionMetadata.data.isNotEmpty) {
      queryParams['execution_metadata'] = executionMetadata.toQueryParams();
    }

    if (issues != null && issues.isNotEmpty) {
      queryParams['issues'] = issues;
    }

    if (fromDate != null) {
      queryParams['from_date'] = fromDate.toIso8601String();
    }
    if (untilDate != null) {
      queryParams['until_date'] = untilDate.toIso8601String();
    }

    // Add pagination
    queryParams['limit'] = limit ?? 500;
    queryParams['offset'] = offset ?? 0;

    final response =
        await dio.get('/v1/test-results', queryParameters: queryParams);

    final jsonData = response.data as Map<String, dynamic>;
    final resultsList =
        (jsonData['test_results'] as List).cast<Map<String, dynamic>>();

    final testResults = resultsList
        .map((jsonResult) => TestResultWithContext.fromJson(jsonResult))
        .toList();

    return TestResultsSearchResult(
      count: jsonData['count'] as int,
      testResults: testResults,
    );
  }

  Future<Issue> attachIssueToTestResults({
    required int issueId,
    required List<int> testResultIds,
  }) async {
    final response = await dio.post(
      '/v1/issues/$issueId/attach',
      data: {
        'test_results': testResultIds,
      },
    );
    return Issue.fromJson(response.data);
  }

  Future<Issue> detachIssueFromTestResults({
    required int issueId,
    required List<int> testResultIds,
  }) async {
    final response = await dio.post(
      '/v1/issues/$issueId/detach',
      data: {
        'test_results': testResultIds,
      },
    );
    return Issue.fromJson(response.data);
  }

  Future<List<Issue>> getIssues() async {
    final response = await dio.get('/v1/issues');
    final Map issuesJson = response.data;
    return (issuesJson['issues'] as List)
        .map((json) => Issue.fromJson(json))
        .toList();
  }

  Future<Issue> createIssue({
    required String url,
    String? title,
    String? description,
    String? status,
  }) async {
    final response = await dio.put(
      '/v1/issues',
      data: {
        'url': url,
        if (title != null) 'title': title,
        if (description != null) 'description': description,
        if (status != null) 'status': status,
      },
    );
    return Issue.fromJson(response.data);
  }

  Future<User?> getCurrentUser() async {
    final response = await dio.get('/v1/users/me');
    final data = response.data;
    if (data == null) {
      return null;
    }
    return User.fromJson(response.data);
  }

  Future<ExecutionMetadata> getExecutionMetadata() async {
    final response = await dio.get('/v1/execution-metadata');
    return ExecutionMetadata.fromJson(response.data['execution_metadata']);
  }
}
