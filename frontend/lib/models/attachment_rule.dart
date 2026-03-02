// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:freezed_annotation/freezed_annotation.dart';

import 'execution_metadata.dart';
import 'attachment_rule_filters.dart';
import 'test_result.dart';

part 'attachment_rule.freezed.dart';
part 'attachment_rule.g.dart';

@freezed
abstract class AttachmentRule with _$AttachmentRule {
  const AttachmentRule._();
  const factory AttachmentRule({
    required int id,
    required bool enabled,
    @JsonKey(name: 'families') @Default([]) List<String> families,
    @JsonKey(name: 'environment_names')
    @Default([])
    List<String> environmentNames,
    @JsonKey(name: 'test_case_names') @Default([]) List<String> testCaseNames,
    @JsonKey(name: 'template_ids') @Default([]) List<String> templateIds,
    @JsonKey(name: 'execution_metadata')
    @Default(ExecutionMetadata())
    ExecutionMetadata executionMetadata,
    @JsonKey(name: 'test_result_statuses')
    @Default([])
    List<TestResultStatus> testResultStatuses,
  }) = _AttachmentRule;

  factory AttachmentRule.fromJson(Map<String, Object?> json) =>
      _$AttachmentRuleFromJson(json);

  AttachmentRuleFilters toFilters() {
    return AttachmentRuleFilters(
      families: families,
      environmentNames: environmentNames,
      testCaseNames: testCaseNames,
      templateIds: templateIds,
      testResultStatuses: testResultStatuses,
      executionMetadata: executionMetadata,
    );
  }
}
