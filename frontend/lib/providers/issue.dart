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

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/issue.dart';
import '../models/attachment_rule.dart';
import '../models/attachment_rule_filters.dart';
import '../models/test_results_filters.dart';
import 'api.dart';

part 'issue.g.dart';

@riverpod
class Issue extends _$Issue {
  @override
  Future<IssueWithContext> build(int issueId) async {
    final api = ref.watch(apiProvider);
    return await api.getIssue(issueId);
  }

  Future<AttachmentRule> createAttachmentRule({
    required int issueId,
    required bool enabled,
    required AttachmentRuleFilters filters,
  }) async {
    final api = ref.read(apiProvider);
    final attachmentRule = await api.createAttachmentRule(
      issueId: issueId,
      enabled: enabled,
      filters: filters,
    );
    final issue = await future;
    final index = issue.attachmentRules
        .indexWhere((rule) => rule.id == attachmentRule.id);
    List<AttachmentRule> updatedAttachmentRules;
    if (index != -1) {
      updatedAttachmentRules = List<AttachmentRule>.from(issue.attachmentRules);
      updatedAttachmentRules[index] = attachmentRule;
    } else {
      updatedAttachmentRules = [...issue.attachmentRules, attachmentRule];
    }
    state = AsyncData(
      issue.copyWith(
        attachmentRules: updatedAttachmentRules,
      ),
    );
    return attachmentRule;
  }

  Future<void> deleteAttachmentRule({
    required int issueId,
    required int attachmentRuleId,
  }) async {
    final api = ref.read(apiProvider);
    await api.deleteAttachmentRule(
      issueId: issueId,
      attachmentRuleId: attachmentRuleId,
    );
    final issue = await future;
    final updatedAttachmentRules = issue.attachmentRules
        .where((rule) => rule.id != attachmentRuleId)
        .toList();
    state = AsyncData(
      issue.copyWith(
        attachmentRules: updatedAttachmentRules,
      ),
    );
  }

  Future<void> enableAttachmentRule({
    required int issueId,
    required int attachmentRuleId,
  }) async {
    final api = ref.read(apiProvider);
    await api.patchAttachmentRule(
      issueId: issueId,
      attachmentRuleId: attachmentRuleId,
      enabled: true,
    );
    final issue = await future;
    final updatedAttachmentRules = issue.attachmentRules
        .map(
          (rule) =>
              rule.id == attachmentRuleId ? rule.copyWith(enabled: true) : rule,
        )
        .toList();
    state = AsyncData(
      issue.copyWith(
        attachmentRules: updatedAttachmentRules,
      ),
    );
  }

  Future<void> disableAttachmentRule({
    required int issueId,
    required int attachmentRuleId,
  }) async {
    final api = ref.read(apiProvider);
    await api.patchAttachmentRule(
      issueId: issueId,
      attachmentRuleId: attachmentRuleId,
      enabled: false,
    );
    final issue = await future;
    final updatedAttachmentRules = issue.attachmentRules
        .map(
          (rule) => rule.id == attachmentRuleId
              ? rule.copyWith(enabled: false)
              : rule,
        )
        .toList();
    state = AsyncData(
      issue.copyWith(
        attachmentRules: updatedAttachmentRules,
      ),
    );
  }

  Future<void> attachIssueToTestResults({
    required int issueId,
    required TestResultsFilters filters,
    int? attachmentRuleId,
  }) async {
    final api = ref.read(apiProvider);
    await api.attachIssue(
      issueId: issueId,
      filters: filters,
      attachmentRuleId: attachmentRuleId,
    );
  }

  Future<void> detachIssueFromTestResults({
    required int issueId,
    required TestResultsFilters filters,
  }) async {
    final api = ref.read(apiProvider);
    await api.detachIssue(
      issueId: issueId,
      filters: filters,
    );
  }

  Future<void> setAutoRerun({
    required int issueId,
    required bool enabled,
  }) async {
    final api = ref.read(apiProvider);
    final updatedIssue = await api.patchIssueAutoRerun(
      issueId: issueId,
      autoRerunEnabled: enabled,
    );
    state = AsyncData(updatedIssue);
  }
}
