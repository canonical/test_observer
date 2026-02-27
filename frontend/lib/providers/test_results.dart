// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_result.dart';
import '../models/issue_attachment.dart';
import '../models/attachment_rule.dart';
import 'api.dart';

part 'test_results.g.dart';

@riverpod
class TestResults extends _$TestResults {
  @override
  Future<List<TestResult>> build(int testExecutionId) async {
    final api = ref.watch(apiProvider);
    return await api.getTestExecutionResults(testExecutionId);
  }

  Future<void> attachIssueToTestResult(
    int testResultId,
    int issueId, {
    AttachmentRule? attachmentRule,
  }) async {
    final api = ref.read(apiProvider);
    final attachedIssue = await api.attachIssue(
      issueId: issueId,
      testResultIds: [testResultId],
      attachmentRuleId: attachmentRule?.id,
    );
    final testResults = await future;
    final resultIndex =
        testResults.indexWhere((result) => result.id == testResultId);
    if (resultIndex == -1) {
      return;
    }
    final testResult = testResults[resultIndex];
    final attachments = testResult.issueAttachments;
    final alreadyAttached = attachments
        .any((attachment) => attachment.issue.id == attachedIssue.id);
    if (alreadyAttached) {
      return;
    }
    // Create a new attachment for the issue
    final newAttachment =
        IssueAttachment(issue: attachedIssue, attachmentRule: attachmentRule);
    final updatedAttachments = [...attachments, newAttachment];
    final updatedTestResult =
        testResult.copyWith(issueAttachments: updatedAttachments);
    final updatedTestResults = List<TestResult>.from(testResults);
    updatedTestResults[resultIndex] = updatedTestResult;
    state = AsyncData(updatedTestResults);
  }

  Future<void> detachIssueFromTestResult(int testResultId, int issueId) async {
    final api = ref.read(apiProvider);
    await api.detachIssue(
      issueId: issueId,
      testResultIds: [testResultId],
    );
    final testResults = await future;
    final resultIndex =
        testResults.indexWhere((result) => result.id == testResultId);
    if (resultIndex == -1) {
      return;
    }
    final testResult = testResults[resultIndex];
    final attachments = testResult.issueAttachments;
    final updatedAttachments = attachments
        .where((attachment) => attachment.issue.id != issueId)
        .toList();
    final updatedTestResult =
        testResult.copyWith(issueAttachments: updatedAttachments);
    final updatedTestResults = List<TestResult>.from(testResults);
    updatedTestResults[resultIndex] = updatedTestResult;
    state = AsyncData(updatedTestResults);
  }
}
