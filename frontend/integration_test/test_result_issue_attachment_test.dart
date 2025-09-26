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
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/attachment_rule_filters.dart';
import 'package:testcase_dashboard/models/attachment_rule.dart';
import 'package:testcase_dashboard/models/issue_attachment.dart';
import 'package:testcase_dashboard/models/issue.dart';
import 'package:testcase_dashboard/models/stage_name.dart';
import 'package:testcase_dashboard/models/detailed_test_results.dart';
import 'package:testcase_dashboard/models/test_result.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/artefact_page/issue_attachments/issue_attachments_expandable.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {
  TestResult dummyTestResult = TestResult(
    id: 1,
    name: 'Sample Test Result',
    status: TestResultStatus.passed,
    issueAttachments: [],
    createdAt: DateTime.now(),
  );

  final dummyIssue = IssueWithContext(
    id: 123,
    url: 'https://github.com/canonical/test_observer/issues/123',
    status: IssueStatus.open,
    source: IssueSource.github,
    project: '',
    key: '',
    title: 'Dummy Issue',
    attachmentRules: [],
  );

  final dummyArtefact = Artefact(
    id: 1,
    name: 'artefact',
    version: '1',
    track: 'latest',
    family: 'snap',
    store: 'ubuntu',
    series: '',
    repo: '',
    status: ArtefactStatus.undecided,
    comment: '',
    stage: StageName.beta,
    bugLink: '',
    allEnvironmentReviewsCount: 1,
    completedEnvironmentReviewsCount: 0,
  );

  final dummyAttachmentRule = AttachmentRule(
    id: 1,
    enabled: true,
    testCaseNames: ['Sample Test Result'],
  );

  bool attachmentRuleCreated = false;

  @override
  Future<List<Issue>> getIssues() async {
    return [dummyIssue.toIssue()];
  }

  @override
  Future<Issue> createIssue({
    required String url,
    String? title,
    String? description,
    String? status,
  }) async {
    return dummyIssue.toIssue();
  }

  @override
  Future<List<TestResult>> getTestExecutionResults(int testExecutionId) async {
    return [dummyTestResult];
  }

  @override
  Future<Issue> attachIssue({
    required int issueId,
    List<int>? testResultIds,
    TestResultsFilters? filters,
    int? attachmentRuleId,
  }) async {
    for (final id in testResultIds ?? []) {
      if (id == dummyTestResult.id) {
        final updatedAttachments =
            List<IssueAttachment>.from(dummyTestResult.issueAttachments)
              ..add(IssueAttachment(issue: dummyIssue.toIssue()));
        dummyTestResult =
            dummyTestResult.copyWith(issueAttachments: updatedAttachments);
      }
    }
    return dummyIssue.toIssue();
  }

  @override
  Future<Issue> detachIssue({
    required int issueId,
    List<int>? testResultIds,
    TestResultsFilters? filters,
    int? attachmentRuleId,
  }) async {
    for (final id in testResultIds ?? []) {
      if (id == dummyTestResult.id) {
        final updatedAttachments =
            List<IssueAttachment>.from(dummyTestResult.issueAttachments)
              ..removeWhere((attachment) => attachment.issue.id == issueId);
        dummyTestResult =
            dummyTestResult.copyWith(issueAttachments: updatedAttachments);
      }
    }
    return dummyIssue.toIssue();
  }

  @override
  Future<Artefact> getArtefact(int artefactId) async {
    return dummyArtefact;
  }

  @override
  Future<AttachmentRule> createAttachmentRule({
    required int issueId,
    required bool enabled,
    required AttachmentRuleFilters filters,
  }) async {
    attachmentRuleCreated = true;
    return dummyAttachmentRule;
  }

  @override
  Future<TestResultsSearchResult> searchTestResults(
    TestResultsFilters filters,
  ) async {
    return TestResultsSearchResult(count: 0, testResults: []);
  }

  @override
  Future<IssueWithContext> getIssue(int issueId) async {
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
            artefactId: 1,
            initiallyExpanded: true,
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
      urlField,
      'https://github.com/canonical/test-observer/issues/123',
    );

    // Tap the attach button in the dialog
    final dialogAttachButton =
        find.byKey(const Key('attachIssueFormSubmitButton'));
    expect(dialogAttachButton, findsOneWidget);
    await tester.tap(dialogAttachButton);
    await tester.pump();
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
            artefactId: 1,
            initiallyExpanded: true,
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

  testWidgets('Attach and create attachment rule', (tester) async {
    final apiMock = ApiRepositoryMock();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [apiProvider.overrideWithValue(apiMock)],
        child: MaterialApp(
          home: IssueAttachmentsExpandable(
            testExecutionId: 1,
            testResultId: 1,
            artefactId: 1,
            initiallyExpanded: true,
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
      urlField,
      'https://github.com/canonical/test-observer/issues/123',
    );

    // Find the "Create attachment rule" checkbox and select it
    final createRuleCheckbox =
        find.byKey(const Key('createAttachmentRuleCheckbox'));
    expect(createRuleCheckbox, findsOneWidget);
    await tester.tap(createRuleCheckbox);
    await tester.pumpAndSettle();

    // Find the "test plan" checkbox and select it
    final testPlanCheckbox = find.text('Sample Test Result');
    expect(testPlanCheckbox, findsOneWidget);
    await tester.tap(testPlanCheckbox);
    await tester.pumpAndSettle();

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

    // Assert that the attachment rule was created
    expect(apiMock.attachmentRuleCreated, isTrue);

    // Assert that the issue attachment is attributed to the attachment rule
    expect(find.byTooltip('Attached by a rule'), findsOneWidget);
  });
}
