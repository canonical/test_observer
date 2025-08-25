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

import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/issue_attachment.dart';
import 'api.dart';
import 'test_results.dart';

part 'test_result_issue_attachments.g.dart';

@riverpod
class TestResultIssueAttachments extends _$TestResultIssueAttachments {
  @override
  Future<List<IssueAttachment>> build({
    required int testExecutionId,
    required int testResultId,
  }) async {
    // Use the testResults provider for consistency
    final testResults =
        await ref.watch(testResultsProvider(testExecutionId).future);
    final result = testResults.firstWhere(
      (r) => r.id == testResultId,
      orElse: () => throw Exception('TestResult not found'),
    );
    return result.issueAttachments;
  }

  Future<void> attachIssueToTestResult({
    required int issueId,
    required int testResultId,
  }) async {
    final api = ref.read(apiProvider);
    await api.attachIssueToTestResults(
      issueId: issueId,
      testResultIds: [testResultId],
    );
    ref.invalidateSelf();
    ref.invalidate(testResultsProvider(testResultId));
  }

  Future<void> detachIssueFromTestResult({
    required int issueId,
    required int testResultId,
  }) async {
    final api = ref.read(apiProvider);
    await api.detachIssueFromTestResults(
      issueId: issueId,
      testResultIds: [testResultId],
    );
    ref.invalidateSelf();
    ref.invalidate(testResultsProvider(testResultId));
  }
}
