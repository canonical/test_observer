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

import 'package:dartx/dartx.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'execution_metadata.dart';
import '../routing.dart';
import 'test_result.dart';

part 'test_results_filters.freezed.dart';
part 'test_results_filters.g.dart';

// Code generator for the TestResultsFilters class will not call IntListFilter.fromJson
// but instead uses the instance which does not work properly.
class IntListFilterConverter implements JsonConverter<IntListFilter, dynamic> {
  const IntListFilterConverter();

  @override
  IntListFilter fromJson(dynamic json) {
    if (json is String) {
      if (json == 'any') return const IntListFilter.any();
      if (json == 'none') return const IntListFilter.none();
    }
    if (json is List) {
      return IntListFilter.list(json.cast<int>());
    }
    return const IntListFilter.list([]);
  }

  @override
  dynamic toJson(IntListFilter filter) {
    return switch (filter) {
      _IntListFilterList(:final values) => values,
      _IntListFilterAny() => 'any',
      _IntListFilterNone() => 'none',
    };
  }
}

@freezed
sealed class IntListFilter with _$IntListFilter {
  // ignore: unused_element
  const IntListFilter._();
  const factory IntListFilter.list(List<int> values) = _IntListFilterList;
  const factory IntListFilter.any() = _IntListFilterAny;
  const factory IntListFilter.none() = _IntListFilterNone;

  factory IntListFilter.fromJson(Map<String, Object?> json) =>
      _$IntListFilterFromJson(json);

  // Helper methods to extract values
  List<int> get values => switch (this) {
        _IntListFilterList(:final values) => values,
        _ => [],
      };

  bool get isAny => this is _IntListFilterAny;
  bool get isNone => this is _IntListFilterNone;
  bool get isList => this is _IntListFilterList;

  bool get isNotEmpty => switch (this) {
        _IntListFilterList(:final values) => values.isNotEmpty,
        _ => true,
      };

  bool get isEmpty => !isNotEmpty;

  static IntListFilter fromQueryParam(List<String> params) {
    if (params.length == 1 && params.first == 'any') {
      return const IntListFilter.any();
    } else if (params.length == 1 && params.first == 'none') {
      return const IntListFilter.none();
    } else {
      return IntListFilter.list(
        params.map((s) => int.tryParse(s)).whereNotNull().toList(),
      );
    }
  }

  List<String> toQueryParam() {
    return switch (this) {
      _IntListFilterList(:final values) when values.isNotEmpty =>
        values.map((i) => i.toString()).toList(),
      _IntListFilterAny() => ['any'],
      _IntListFilterNone() => ['none'],
      _ => [],
    };
  }
}

// Code generator for the TestResultsFilters class will not call ExecutionMetadata.fromJson
// but instead uses the instance which does not work properly.
class ExecutionMetadataConverter
    implements JsonConverter<ExecutionMetadata, Map<String, dynamic>> {
  const ExecutionMetadataConverter();

  @override
  ExecutionMetadata fromJson(Map<String, dynamic> json) {
    return ExecutionMetadata.fromJson(json);
  }

  @override
  Map<String, dynamic> toJson(ExecutionMetadata metadata) {
    return metadata.toJson();
  }
}

@freezed
abstract class TestResultsFilters with _$TestResultsFilters {
  const TestResultsFilters._();
  const factory TestResultsFilters({
    @Default([]) List<String> families,
    @JsonKey(name: 'test_result_statuses')
    @Default([])
    List<TestResultStatus> testResultStatuses,
    @Default([]) List<String> artefacts,
    @JsonKey(name: 'artefact_is_archived') bool? artefactIsArchived,
    @Default([]) List<String> environments,
    @JsonKey(name: 'test_cases') @Default([]) List<String> testCases,
    @JsonKey(name: 'template_ids') @Default([]) List<String> templateIds,
    @JsonKey(name: 'execution_metadata')
    @ExecutionMetadataConverter()
    @Default(ExecutionMetadata())
    ExecutionMetadata executionMetadata,
    @IntListFilterConverter()
    @Default(IntListFilter.list([]))
    IntListFilter issues,
    @IntListFilterConverter()
    @Default(IntListFilter.list([]))
    IntListFilter assignees,
    @JsonKey(name: 'from_date') DateTime? fromDate,
    @JsonKey(name: 'until_date') DateTime? untilDate,
    int? offset,
    int? limit,
  }) = _TestResultsFilters;

  factory TestResultsFilters.fromJson(Map<String, Object?> json) =>
      _$TestResultsFiltersFromJson(json);

  factory TestResultsFilters.fromQueryParams(
    Map<String, List<String>> parameters,
  ) {
    List<String> parseParam(List<String>? values) {
      if (values == null || values.isEmpty) return <String>[];

      // Handle both formats:
      // 1. Multiple list entries: ['value1', 'value2']
      // 2. Comma-separated in single entry: ['value1,value2']
      return values
          .expand((v) => v.split(','))
          .map((s) => s.trim())
          .where((s) => s.isNotEmpty)
          .toList();
    }

    final families = parseParam(parameters['families']);
    final testResultStatuses = parseParam(parameters['test_result_statuses'])
        .map((s) => TestResultStatus.fromString(s))
        .toList();
    final artefacts = parseParam(parameters['artefacts']);
    final artefactIsArchived = parseParam(parameters['artefact_is_archived'])
        .map((s) => s.toLowerCase() == 'true')
        .firstOrNull;
    final environments = parseParam(parameters['environments']);
    final testCases = parseParam(parameters['test_cases']);
    final templateIds = parseParam(parameters['template_ids']);
    final executionMetadata = ExecutionMetadata.fromQueryParams(
      parameters['execution_metadata'],
    );
    final issues = IntListFilter.fromQueryParam(
      parseParam(parameters['issues']),
    );
    final assignees = IntListFilter.fromQueryParam(
      parseParam(parameters['assignee_ids']),
    );
    final fromDate = parseParam(parameters['from_date'])
        .map((s) => DateTime.tryParse(s))
        .firstOrNullWhere((v) => v != null);
    final untilDate = parseParam(parameters['until_date'])
        .map((s) => DateTime.tryParse(s))
        .firstOrNullWhere((v) => v != null);
    final offset = parseParam(parameters['offset'])
        .map((s) => int.tryParse(s))
        .firstOrNullWhere((v) => v != null);
    final limit = parseParam(parameters['limit'])
        .map((s) => int.tryParse(s))
        .firstOrNullWhere((v) => v != null);

    return TestResultsFilters(
      families: families,
      testResultStatuses: testResultStatuses,
      artefacts: artefacts,
      artefactIsArchived: artefactIsArchived,
      environments: environments,
      testCases: testCases,
      templateIds: templateIds,
      executionMetadata: executionMetadata,
      issues: issues,
      assignees: assignees,
      fromDate: fromDate,
      untilDate: untilDate,
      offset: offset,
      limit: limit,
    );
  }

  Map<String, List<String>> toQueryParams() {
    final params = <String, List<String>>{};
    if (families.isNotEmpty) {
      params['families'] = families;
    }
    if (testResultStatuses.isNotEmpty) {
      params['test_result_statuses'] =
          testResultStatuses.map((s) => s.name.toUpperCase()).toList();
    }
    if (artefacts.isNotEmpty) {
      params['artefacts'] = artefacts;
    }
    if (artefactIsArchived != null) {
      params['artefact_is_archived'] = [artefactIsArchived.toString()];
    }
    if (environments.isNotEmpty) {
      params['environments'] = environments;
    }
    if (testCases.isNotEmpty) {
      params['test_cases'] = testCases;
    }
    if (templateIds.isNotEmpty) {
      params['template_ids'] = templateIds;
    }
    if (executionMetadata.data.isNotEmpty) {
      params['execution_metadata'] = executionMetadata.toQueryParams();
    }
    final issuesParam = issues.toQueryParam();
    if (issuesParam.isNotEmpty) {
      params['issues'] = issuesParam;
    }
    final assigneesParam = assignees.toQueryParam();
    if (assigneesParam.isNotEmpty) {
      params['assignee_ids'] = assigneesParam;
    }
    if (fromDate != null) {
      params['from_date'] = [fromDate!.toIso8601String()];
    }
    if (untilDate != null) {
      params['until_date'] = [untilDate!.toIso8601String()];
    }
    if (offset != null) {
      params['offset'] = [offset!.toString()];
    }
    if (limit != null) {
      params['limit'] = [limit!.toString()];
    }
    return params;
  }

  bool get hasFilters =>
      families.isNotEmpty ||
      testResultStatuses.isNotEmpty ||
      artefacts.isNotEmpty ||
      artefactIsArchived != null ||
      environments.isNotEmpty ||
      testCases.isNotEmpty ||
      templateIds.isNotEmpty ||
      executionMetadata.isNotEmpty ||
      issues.isNotEmpty ||
      assignees.isNotEmpty ||
      fromDate != null ||
      untilDate != null;

  Uri toTestResultsUri() {
    return Uri(
      path: AppRoutes.testResults,
      queryParameters:
          toQueryParams().map((key, value) => MapEntry(key, value.join(','))),
    );
  }
}
