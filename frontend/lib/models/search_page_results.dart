// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'execution_metadata.dart';
import 'family_name.dart';
import 'issue.dart';
import 'test_execution.dart';
import 'test_result.dart';

/// Compact table response used only by the Search page.
class SearchPageTableResponse {
  const SearchPageTableResponse({
    required this.count,
    required this.limit,
    required this.offset,
    required this.rows,
  });

  final int? count;
  final int limit;
  final int offset;
  final List<SearchPageTableRow> rows;

  factory SearchPageTableResponse.fromJson(Map<String, dynamic> json) {
    return SearchPageTableResponse(
      count: json['count'] as int?,
      limit: json['limit'] as int,
      offset: json['offset'] as int,
      rows:
          (json['rows'] as List<dynamic>)
              .map(
                (row) =>
                    SearchPageTableRow.fromJson(row as Map<String, dynamic>),
              )
              .toList(),
    );
  }
}

class SearchPageTableRow {
  const SearchPageTableRow({
    required this.testResult,
    required this.testExecution,
    required this.artefact,
    required this.artefactBuild,
  });

  final SearchPageTableTestResult testResult;
  final SearchPageTableTestExecution testExecution;
  final SearchPageTableArtefact artefact;
  final SearchPageTableArtefactBuild artefactBuild;

  factory SearchPageTableRow.fromJson(Map<String, dynamic> json) {
    return SearchPageTableRow(
      testResult: SearchPageTableTestResult.fromJson(
        json['test_result'] as Map<String, dynamic>,
      ),
      testExecution: SearchPageTableTestExecution.fromJson(
        json['test_execution'] as Map<String, dynamic>,
      ),
      artefact: SearchPageTableArtefact.fromJson(
        json['artefact'] as Map<String, dynamic>,
      ),
      artefactBuild: SearchPageTableArtefactBuild.fromJson(
        json['artefact_build'] as Map<String, dynamic>,
      ),
    );
  }
}

class SearchPageTableTestResult {
  const SearchPageTableTestResult({
    required this.id,
    required this.name,
    required this.category,
    required this.createdAt,
    required this.templateId,
    required this.status,
  });

  final int id;
  final String name;
  final String category;
  final DateTime createdAt;
  final String templateId;
  final TestResultStatus status;

  factory SearchPageTableTestResult.fromJson(Map<String, dynamic> json) {
    return SearchPageTableTestResult(
      id: json['id'] as int,
      name: json['name'] as String,
      category: json['category'] as String,
      createdAt: DateTime.parse(json['created_at'] as String),
      templateId: json['template_id'] as String,
      status: TestResultStatus.fromString(json['status'] as String),
    );
  }
}

class SearchPageTableTestExecution {
  const SearchPageTableTestExecution({
    required this.id,
    required this.status,
    required this.environment,
    required this.testPlan,
  });

  final int id;
  final TestExecutionStatus status;
  final SearchPageTableEnvironment environment;
  final String testPlan;

  factory SearchPageTableTestExecution.fromJson(Map<String, dynamic> json) {
    return SearchPageTableTestExecution(
      id: json['id'] as int,
      status: _executionStatus(json['status'] as String),
      environment: SearchPageTableEnvironment.fromJson(
        json['environment'] as Map<String, dynamic>,
      ),
      testPlan: json['test_plan'] as String,
    );
  }
}

class SearchPageDetailsTestExecution extends SearchPageTableTestExecution {
  const SearchPageDetailsTestExecution({
    required super.id,
    required super.status,
    required super.environment,
    required super.testPlan,
    required this.executionMetadata,
    required this.createdAt,
  });

  final ExecutionMetadata executionMetadata;
  final DateTime createdAt;

  factory SearchPageDetailsTestExecution.fromJson(Map<String, dynamic> json) {
    final tableFields = SearchPageTableTestExecution.fromJson(json);
    return SearchPageDetailsTestExecution(
      id: tableFields.id,
      status: tableFields.status,
      environment: tableFields.environment,
      testPlan: tableFields.testPlan,
      executionMetadata: _executionMetadata(json['execution_metadata']),
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class SearchPageTableEnvironment {
  const SearchPageTableEnvironment({required this.name});

  final String name;

  factory SearchPageTableEnvironment.fromJson(Map<String, dynamic> json) {
    return SearchPageTableEnvironment(name: json['name'] as String);
  }
}

class SearchPageTableArtefact {
  const SearchPageTableArtefact({
    required this.id,
    required this.name,
    required this.version,
    required this.track,
    required this.family,
  });

  final int id;
  final String name;
  final String version;
  final String track;
  final FamilyName family;

  factory SearchPageTableArtefact.fromJson(Map<String, dynamic> json) {
    return SearchPageTableArtefact(
      id: json['id'] as int,
      name: json['name'] as String,
      version: json['version'] as String,
      track: json['track'] as String,
      family: FamilyName.values.firstWhere(
        (family) => family.name == (json['family'] as String).toLowerCase(),
      ),
    );
  }
}

class SearchPageTableArtefactBuild {
  const SearchPageTableArtefactBuild({required this.architecture});

  final String architecture;

  factory SearchPageTableArtefactBuild.fromJson(Map<String, dynamic> json) {
    return SearchPageTableArtefactBuild(
      architecture: json['architecture'] as String,
    );
  }
}

class SearchPageDetailsResponse {
  const SearchPageDetailsResponse({
    required this.testResult,
    required this.testExecution,
    required this.artefact,
    required this.artefactBuild,
  });

  final SearchPageDetailsTestResult testResult;
  final SearchPageDetailsTestExecution testExecution;
  final SearchPageDetailsArtefact artefact;
  final SearchPageTableArtefactBuild artefactBuild;

  factory SearchPageDetailsResponse.fromJson(Map<String, dynamic> json) {
    return SearchPageDetailsResponse(
      testResult: SearchPageDetailsTestResult.fromJson(
        json['test_result'] as Map<String, dynamic>,
      ),
      testExecution: SearchPageDetailsTestExecution.fromJson(
        json['test_execution'] as Map<String, dynamic>,
      ),
      artefact: SearchPageDetailsArtefact.fromJson(
        json['artefact'] as Map<String, dynamic>,
      ),
      artefactBuild: SearchPageTableArtefactBuild.fromJson(
        json['artefact_build'] as Map<String, dynamic>,
      ),
    );
  }
}

class SearchPageDetailsTestResult {
  const SearchPageDetailsTestResult({
    required this.id,
    required this.name,
    required this.category,
    required this.templateId,
    required this.status,
    required this.ioLog,
    required this.issues,
  });

  final int id;
  final String name;
  final String category;
  final String templateId;
  final TestResultStatus status;
  final String ioLog;
  final List<SearchPageDetailsIssue> issues;

  factory SearchPageDetailsTestResult.fromJson(Map<String, dynamic> json) {
    return SearchPageDetailsTestResult(
      id: json['id'] as int,
      name: json['name'] as String,
      category: json['category'] as String,
      templateId: json['template_id'] as String,
      status: TestResultStatus.fromString(json['status'] as String),
      ioLog: json['io_log'] as String,
      issues:
          (json['issues'] as List<dynamic>)
              .map(
                (attachment) => SearchPageDetailsIssue.fromJson(
                  (attachment as Map<String, dynamic>)['issue']
                      as Map<String, dynamic>,
                ),
              )
              .toList(),
    );
  }
}

class SearchPageDetailsIssue {
  const SearchPageDetailsIssue({
    required this.id,
    required this.source,
    required this.project,
    required this.key,
    required this.title,
    required this.status,
    required this.url,
  });

  final int id;
  final IssueSource source;
  final String project;
  final String key;
  final String title;
  final IssueStatus status;
  final String url;

  factory SearchPageDetailsIssue.fromJson(Map<String, dynamic> json) {
    return SearchPageDetailsIssue(
      id: json['id'] as int,
      source: IssueSource.values.byName(json['source'] as String),
      project: json['project'] as String,
      key: json['key'] as String,
      title: json['title'] as String,
      status: IssueStatus.values.byName(json['status'] as String),
      url: json['url'] as String,
    );
  }
}

class SearchPageDetailsArtefact extends SearchPageTableArtefact {
  const SearchPageDetailsArtefact({
    required super.id,
    required super.name,
    required super.version,
    required super.track,
    required super.family,
  });

  factory SearchPageDetailsArtefact.fromJson(Map<String, dynamic> json) {
    return SearchPageDetailsArtefact(
      id: json['id'] as int,
      name: json['name'] as String,
      version: json['version'] as String,
      track: json['track'] as String,
      family: FamilyName.values.firstWhere(
        (family) => family.name == (json['family'] as String).toLowerCase(),
      ),
    );
  }
}

class SearchPageResultsState {
  const SearchPageResultsState({required this.count, required this.rows});

  final int count;
  final List<SearchPageTableRow> rows;

  bool get hasMore => count > rows.length;
}

TestExecutionStatus _executionStatus(String value) {
  return switch (value) {
    'NOT_STARTED' => TestExecutionStatus.notStarted,
    'IN_PROGRESS' => TestExecutionStatus.inProgress,
    'PASSED' => TestExecutionStatus.passed,
    'FAILED' => TestExecutionStatus.failed,
    'NOT_TESTED' => TestExecutionStatus.notTested,
    'ENDED_PREMATURELY' => TestExecutionStatus.endedPrematurely,
    _ =>
      throw ArgumentError.value(
        value,
        'status',
        'Unknown test execution status',
      ),
  };
}

ExecutionMetadata _executionMetadata(dynamic value) {
  return ExecutionMetadata.fromJson((value as Map).cast<String, Object?>());
}
