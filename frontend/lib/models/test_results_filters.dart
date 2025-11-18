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

@freezed
abstract class TestResultsFilters with _$TestResultsFilters {
  const TestResultsFilters._();
  const factory TestResultsFilters({
    @Default([]) List<String> families,
    @Default([]) List<TestResultStatus> testResultStatuses,
    @Default([]) List<String> artefacts,
    @Default([]) List<String> environments,
    @JsonKey(name: 'test_cases') @Default([]) List<String> testCases,
    @JsonKey(name: 'template_ids') @Default([]) List<String> templateIds,
    @JsonKey(name: 'execution_metadata')
    @Default(ExecutionMetadata())
    ExecutionMetadata executionMetadata,
    @Default([]) List<int> issues,
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
      return values != null && values.isNotEmpty
          ? values.first
              .split(',')
              .map((s) => s.trim())
              .where((s) => s.isNotEmpty)
              .toList()
          : <String>[];
    }

    final families = parseParam(parameters['families']);
    final testResultStatuses = parseParam(parameters['test_result_statuses'])
        .map((s) => TestResultStatus.fromString(s))
        .toList();
    final artefacts = parseParam(parameters['artefacts']);
    final environments = parseParam(parameters['environments']);
    final testCases = parseParam(parameters['test_cases']);
    final templateIds = parseParam(parameters['template_ids']);
    final executionMetadata = ExecutionMetadata.fromQueryParams(
      parameters['execution_metadata'],
    );
    final issues = parseParam(parameters['issues'])
        .map((s) => int.tryParse(s))
        .whereNotNull()
        .toList();
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
      environments: environments,
      testCases: testCases,
      templateIds: templateIds,
      executionMetadata: executionMetadata,
      issues: issues,
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
    if (issues.isNotEmpty) {
      params['issues'] = issues.map((i) => i.toString()).toList();
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
      environments.isNotEmpty ||
      testCases.isNotEmpty ||
      templateIds.isNotEmpty ||
      executionMetadata.isNotEmpty ||
      issues.isNotEmpty ||
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
