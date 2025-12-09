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

import 'package:freezed_annotation/freezed_annotation.dart';

import 'execution_metadata.dart';
import 'test_results_filters.dart';
import 'attachment_rule.dart';
import 'test_result.dart';

part 'attachment_rule_filters.freezed.dart';
part 'attachment_rule_filters.g.dart';

@freezed
abstract class AttachmentRuleFilters with _$AttachmentRuleFilters {
  const AttachmentRuleFilters._();
  @JsonSerializable(explicitToJson: true)
  const factory AttachmentRuleFilters({
    @JsonKey(name: 'families') @Default([]) List<String> families,
    @JsonKey(name: 'environment_names')
    @Default([])
    List<String> environmentNames,
    @JsonKey(name: 'test_case_names') @Default([]) List<String> testCaseNames,
    @JsonKey(name: 'template_ids') @Default([]) List<String> templateIds,
    @JsonKey(name: 'test_result_statuses')
    @Default([])
    List<TestResultStatus> testResultStatuses,
    @JsonKey(name: 'execution_metadata')
    @Default(ExecutionMetadata())
    ExecutionMetadata executionMetadata,
  }) = _AttachmentRuleFilters;

  factory AttachmentRuleFilters.fromJson(Map<String, dynamic> json) =>
      _$AttachmentRuleFiltersFromJson(json);

  factory AttachmentRuleFilters.fromTestResultsFilters(
    TestResultsFilters filters,
  ) {
    return AttachmentRuleFilters(
      families: filters.families,
      environmentNames: filters.environments,
      testCaseNames: filters.testCases,
      templateIds: filters.templateIds,
      testResultStatuses: filters.testResultStatuses,
      executionMetadata: filters.executionMetadata,
    );
  }

  TestResultsFilters toTestResultsFilters() {
    return TestResultsFilters(
      families: families,
      environments: environmentNames,
      testCases: testCaseNames,
      templateIds: templateIds,
      testResultStatuses: testResultStatuses,
      executionMetadata: executionMetadata,
    );
  }

  static bool areFiltersCompatible(TestResultsFilters filters) {
    return AttachmentRuleFilters.fromTestResultsFilters(filters)
            .toTestResultsFilters() ==
        filters;
  }

  factory AttachmentRuleFilters.fromAttachmentRule(AttachmentRule rule) {
    return AttachmentRuleFilters(
      families: rule.families,
      environmentNames: rule.environmentNames,
      testCaseNames: rule.testCaseNames,
      templateIds: rule.templateIds,
      testResultStatuses: rule.testResultStatuses,
      executionMetadata: rule.executionMetadata,
    );
  }

  get hasFilters {
    return families.isNotEmpty ||
        environmentNames.isNotEmpty ||
        testCaseNames.isNotEmpty ||
        templateIds.isNotEmpty ||
        executionMetadata.isNotEmpty;
  }
}
