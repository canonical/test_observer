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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/issue.dart';
import 'package:testcase_dashboard/models/test_result.dart';
import 'package:testcase_dashboard/models/issue_attachment.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/artefact_page/issue_attachments/issue_attachments_expandable.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {
  TestResult _dummyTestResult = TestResult(
    id: 1,
    name: 'Sample Test Result',
    status: TestResultStatus.passed,
    issueAttachments: [],
  );

  final dummyIssue = Issue(
    id: 123,
    url: 'https://github.com/canonical/test_observer/issues/123',
    status: IssueStatus.open,
    source: IssueSource.github,
    project: '',
    key: '',
    title: 'Dummy Issue',
  );

  @override
  Future<Issue> createIssue({
    required String url,
    String? title,
    String? description,
    String? status,
  }) async {
    return dummyIssue;
  }

  @override
  Future<List<TestResult>> getTestExecutionResults(int testExecutionId) async {
    return [_dummyTestResult];
  }

  @override
  Future<Issue> attachIssueToTestResults({
    required int issueId,
    required List<int> testResultIds,
  }) async {
    for (final id in testResultIds) {
      if (id == _dummyTestResult.id) {
        final updatedAttachments =
            List<IssueAttachment>.from(_dummyTestResult.issueAttachments)
              ..add(IssueAttachment(issue: dummyIssue));
        _dummyTestResult =
            _dummyTestResult.copyWith(issueAttachments: updatedAttachments);
      }
    }
    return dummyIssue;
  }

  @override
  Future<Issue> detachIssueFromTestResults({
    required int issueId,
    required List<int> testResultIds,
  }) async {
    for (final id in testResultIds) {
      if (id == _dummyTestResult.id) {
        final updatedAttachments =
            List<IssueAttachment>.from(_dummyTestResult.issueAttachments)
              ..removeWhere((attachment) => attachment.issue.id == issueId);
        _dummyTestResult =
            _dummyTestResult.copyWith(issueAttachments: updatedAttachments);
      }
    }
    return dummyIssue;
  }
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Attach and detach issue from Test Result', (tester) async {
    final apiMock = ApiRepositoryMock();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiProvider.overrideWithValue(apiMock)],
        child: MaterialApp(
          home: IssueAttachmentsExpandable(
            testExecutionId: 1,
            testResultId: 1,
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Assert that the issue attachment is not present at the start
    expect(find.text('Dummy Issue'), findsNothing);

    // Tap the attach button to open the dialog
    final attachButton = find.byKey(const Key('attachIssueButton'));
    expect(attachButton, findsOneWidget);
    await tester.tap(attachButton);
    await tester.pumpAndSettle();

    // Find the issue URL input field in the dialog and enter a valid URL
    final urlField = find.byKey(const Key('attachIssueFormUrlInput'));
    expect(urlField, findsOneWidget);
    await tester.enterText(
        urlField, 'https://github.com/canonical/test-observer/issues/123',);

    // Tap the attach button in the dialog
    final dialogAttachButton =
        find.byKey(const Key('attachIssueFormSubmitButton'));
    expect(dialogAttachButton, findsOneWidget);
    await tester.tap(dialogAttachButton);
    await tester.pumpAndSettle();

    // Assert that the dialog is closed (form no longer present)
    expect(urlField, findsNothing);

    // Assert that the issue attachment is now present
    expect(find.text('Dummy Issue'), findsOneWidget);

    // Tap the detach button to open the dialog
    final detachButton = find.byKey(const Key('detachIssueButton'));
    expect(detachButton, findsOneWidget);
    await tester.tap(detachButton);
    await tester.pumpAndSettle();

    // Tap the detach button to open the dialog
    final detachConfirmButton =
        find.byKey(const Key('detachIssueConfirmButton'));
    expect(detachConfirmButton, findsOneWidget);
    await tester.tap(detachConfirmButton);
    await tester.pumpAndSettle();

    // Assert that the issue attachment is not present after detaching
    expect(find.text('Dummy Issue'), findsNothing);
  });

  testWidgets('Use existing issue from URL', (tester) async {
    final apiMock = ApiRepositoryMock();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiProvider.overrideWithValue(apiMock)],
        child: MaterialApp(
          home: IssueAttachmentsExpandable(
            testExecutionId: 1,
            testResultId: 1,
          ),
        ),
      ),
    );

    await tester.pumpAndSettle();

    // Assert that the issue attachment is not present at the start
    expect(find.text('Dummy Issue'), findsNothing);

    // Tap the attach button to open the dialog
    final attachButton = find.byKey(const Key('attachIssueButton'));
    expect(attachButton, findsOneWidget);
    await tester.tap(attachButton);
    await tester.pumpAndSettle();

    // Find the issue URL input field in the dialog and enter an existing issue URL
    final urlField = find.byKey(const Key('attachIssueFormUrlInput'));
    expect(urlField, findsOneWidget);
    await tester.enterText(urlField, '${Uri.base.origin}/#/issues/123');

    // Tap the attach button in the dialog
    final dialogAttachButton =
        find.byKey(const Key('attachIssueFormSubmitButton'));
    expect(dialogAttachButton, findsOneWidget);
    await tester.tap(dialogAttachButton);
    await tester.pumpAndSettle();

    // Assert that the dialog is closed (form no longer present)
    expect(urlField, findsNothing);

    // Assert that the issue attachment is now present
    expect(find.text('Dummy Issue'), findsOneWidget);
  });
}
