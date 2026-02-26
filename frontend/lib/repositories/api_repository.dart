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

import 'package:dio/dio.dart';

import '../models/artefact_build.dart';
import '../models/artefact_version.dart';
import '../models/artefact.dart';
import '../models/attachment_rule_filters.dart';
import '../models/attachment_rule.dart';
import '../models/detailed_test_results.dart';
import '../models/environment_issue.dart';
import '../models/environment_review.dart';
import '../models/execution_metadata.dart';
import '../models/family_name.dart';
import '../models/issue.dart';
import '../models/rerun_request.dart';
import '../models/test_event.dart';
import '../models/test_issue.dart';
import '../models/test_result.dart';
import '../models/test_results_filters.dart';
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

  Future<void> startManualTestExecution({
    required String family,
    required String name,
    required String version,
    required String arch,
    required String environment,
    required String testPlan,
    required String initialStatus,
    required Map<String, dynamic> familySpecificFields,
    List<Map<String, String>>? relevantLinks,
  }) async {
    final data = {
      'family': family,
      'name': name,
      'version': version,
      'arch': arch,
      'environment': environment,
      'test_plan': testPlan,
      'initial_status': initialStatus,
      ...familySpecificFields,
    };

    if (relevantLinks != null && relevantLinks.isNotEmpty) {
      data['relevant_links'] = relevantLinks;
    }

    await dio.put(
      '/v1/test-executions/start-test',
      data: data,
    );
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

  Future<void> createReruns({
    List<int>? testExecutionIds,
    TestResultsFilters? filters,
  }) async {
    final data = <String, dynamic>{};
    if (testExecutionIds != null && testExecutionIds.isNotEmpty) {
      data['test_execution_ids'] = testExecutionIds;
    }
    if (filters != null) {
      data['test_results_filters'] = filters.toJson();
    }

    await dio.post(
      '/v1/test-executions/reruns',
      queryParameters: {'silent': true},
      data: data,
    );
  }

  Future<void> deleteReruns({
    List<int>? testExecutionIds,
    TestResultsFilters? filters,
  }) async {
    final data = <String, dynamic>{};
    if (testExecutionIds != null && testExecutionIds.isNotEmpty) {
      data['test_execution_ids'] = testExecutionIds;
    }
    if (filters != null) {
      data['test_results_filters'] = filters.toJson();
    }

    await dio.delete(
      '/v1/test-executions/reruns',
      data: data,
    );
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

  Future<List<String>> searchArtefacts({
    String? query,
    List<String>? families,
    int limit = 50,
    int offset = 0,
  }) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      'offset': offset,
    };

    if (query != null && query.trim().isNotEmpty) {
      queryParams['q'] = query.trim();
    }

    if (families != null && families.isNotEmpty) {
      queryParams['families'] = families;
    }

    final response =
        await dio.get('/v1/artefacts/search', queryParameters: queryParams);
    final Map<String, dynamic> data = response.data;
    final List<dynamic> artefacts = data['artefacts'] ?? [];
    return artefacts.cast<String>();
  }

  Future<List<String>> searchEnvironments({
    String? query,
    List<String>? families,
    int limit = 50,
    int offset = 0,
  }) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      'offset': offset,
    };

    if (query != null && query.trim().isNotEmpty) {
      queryParams['q'] = query.trim();
    }

    if (families != null && families.isNotEmpty) {
      queryParams['families'] = families;
    }

    final response =
        await dio.get('/v1/environments', queryParameters: queryParams);
    final Map<String, dynamic> data = response.data;
    final List<dynamic> environments = data['environments'] ?? [];
    return environments.cast<String>();
  }

  Future<List<String>> searchTestCases({
    String? query,
    List<String>? families,
    int limit = 50,
    int offset = 0,
  }) async {
    final queryParams = <String, dynamic>{
      'limit': limit,
      'offset': offset,
    };

    if (query != null && query.trim().isNotEmpty) {
      queryParams['q'] = query.trim();
    }

    if (families != null && families.isNotEmpty) {
      queryParams['families'] = families;
    }

    final response =
        await dio.get('/v1/test-cases', queryParameters: queryParams);
    final Map<String, dynamic> data = response.data;
    final List<dynamic> testCasesData = data['test_cases'] ?? [];
    return testCasesData.map((item) => item['test_case'] as String).toList();
  }

  Future<TestResultsSearchResult> searchTestResults(
    TestResultsFilters filters,
  ) async {
    final response = await dio.get(
      '/v1/test-results',
      queryParameters: filters.toQueryParams(),
    );
    return TestResultsSearchResult.fromJson(response.data);
  }

  Future<void> submitTestResult({
    required int testExecutionId,
    required String testName,
    required TestResultStatus status,
    String? category,
    String? comment,
    String? ioLog,
  }) async {
    final data = {
      'name': testName,
      'status': status.apiValue,
    };

    if (category != null && category.isNotEmpty) {
      data['category'] = category;
    }

    if (comment != null && comment.isNotEmpty) {
      data['comment'] = comment;
    }

    if (ioLog != null && ioLog.isNotEmpty) {
      data['io_log'] = ioLog;
    }

    await dio.post(
      '/v1/test-executions/$testExecutionId/test-results',
      data: [data],
    );
  }

  Future<Issue> attachIssue({
    required int issueId,
    List<int>? testResultIds,
    TestResultsFilters? filters,
    int? attachmentRuleId,
  }) async {
    final response = await dio.post(
      '/v1/issues/$issueId/attach',
      data: {
        if (testResultIds != null) 'test_results': testResultIds,
        if (filters != null) 'test_results_filters': filters.toJson(),
        if (attachmentRuleId != null) 'attachment_rule': attachmentRuleId,
      },
    );
    return Issue.fromJson(response.data);
  }

  Future<Issue> detachIssue({
    required int issueId,
    List<int>? testResultIds,
    TestResultsFilters? filters,
  }) async {
    final response = await dio.post(
      '/v1/issues/$issueId/detach',
      data: {
        if (testResultIds != null) 'test_results': testResultIds,
        if (filters != null) 'test_results_filters': filters.toJson(),
      },
    );
    return Issue.fromJson(response.data);
  }

  Future<List<Issue>> getIssues({
    String? source,
    String? project,
    String? status,
    int? limit,
    int? offset,
    String? q,
  }) async {
    final response = await dio.get(
      '/v1/issues',
      queryParameters: {
        if (source != null) 'source': source,
        if (project != null) 'project': project,
        if (status != null) 'status': status,
        if (limit != null) 'limit': limit,
        if (offset != null) 'offset': offset,
        if (q != null) 'q': q,
      },
    );
    final Map issuesJson = response.data;
    return (issuesJson['issues'] as List)
        .map((json) => Issue.fromJson(json))
        .toList();
  }

  Future<Issue> createIssue({
    required String url,
    String? title,
    String? status,
  }) async {
    final response = await dio.put(
      '/v1/issues',
      data: {
        'url': url,
        if (title != null) 'title': title,
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

  Future<List<User>> getUsers({
    int? limit,
    int? offset,
    String? q,
  }) async {
    final queryParams = <String, dynamic>{};
    if (limit != null) queryParams['limit'] = limit;
    if (offset != null) queryParams['offset'] = offset;
    if (q != null && q.trim().isNotEmpty) queryParams['q'] = q.trim();

    final response = await dio.get('/v1/users', queryParameters: queryParams);
    final Map<String, dynamic> data = response.data;
    final List<dynamic> users = data['users'] ?? [];
    return users.map((json) => User.fromJson(json)).toList();
  }

  Future<User> getUser(int userId) async {
    final response = await dio.get('/v1/users/$userId');
    return User.fromJson(response.data);
  }

  Future<ExecutionMetadata> getExecutionMetadata() async {
    final response = await dio.get('/v1/execution-metadata');
    return ExecutionMetadata.fromJson(response.data['execution_metadata']);
  }

  Future<IssueWithContext> getIssue(int issueId) async {
    final response = await dio.get('/v1/issues/$issueId');
    return IssueWithContext.fromJson(response.data);
  }

  Future<AttachmentRule> createAttachmentRule({
    required int issueId,
    required bool enabled,
    required AttachmentRuleFilters filters,
  }) async {
    final response = await dio.post(
      '/v1/issues/$issueId/attachment-rules',
      data: {
        'enabled': enabled,
        ...filters.toJson(),
      },
    );
    return AttachmentRule.fromJson(response.data);
  }

  Future<void> deleteAttachmentRule({
    required int issueId,
    required int attachmentRuleId,
  }) async {
    await dio.delete(
      '/v1/issues/$issueId/attachment-rules/$attachmentRuleId',
    );
  }

  Future<void> patchAttachmentRule({
    required int issueId,
    required int attachmentRuleId,
    bool? enabled,
  }) async {
    await dio.patch(
      '/v1/issues/$issueId/attachment-rules/$attachmentRuleId',
      data: {
        if (enabled != null) 'enabled': enabled,
      },
    );
  }
}
