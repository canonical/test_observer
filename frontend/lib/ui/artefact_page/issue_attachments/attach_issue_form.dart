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
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../../models/attachment_rule_filters.dart';
import '../../../models/execution_metadata.dart';
import '../../../models/test_result.dart';
import '../../../models/test_results_filters.dart';
import '../../../providers/artefact_builds.dart';
import '../../../providers/artefact.dart';
import '../../../providers/issues.dart';
import '../../../providers/test_results_search.dart';
import '../../../providers/test_results.dart';
import '../../../routing.dart';
import '../../attachment_rule.dart';
import '../../inline_url_text.dart';
import '../../notification.dart';
import '../../spacing.dart';
import '../../vanilla/vanilla_text_input.dart';

class _AttachIssueForm extends ConsumerStatefulWidget {
  final int testExecutionId;
  final int testResultId;
  final int artefactId;

  const _AttachIssueForm({
    required this.testExecutionId,
    required this.testResultId,
    required this.artefactId,
  });

  @override
  ConsumerState<_AttachIssueForm> createState() => _AttachIssueFormState();
}

class _AttachIssueFormState extends ConsumerState<_AttachIssueForm> {
  late final GlobalKey<FormState> formKey;
  late final TextEditingController urlController;
  bool _createAttachmentRule = false;
  AttachmentRuleFilters _selectedAttachmentRuleFilters =
      AttachmentRuleFilters();

  @override
  void initState() {
    super.initState();
    formKey = GlobalKey<FormState>();
    urlController = TextEditingController();
  }

  @override
  void dispose() {
    urlController.dispose();
    super.dispose();
  }

  Uri _extractRouteUri(Uri uri) {
    return uri.fragment.isNotEmpty ? Uri.parse(uri.fragment) : uri;
  }

  String? _validateUrl(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a URL';
    }
    final uri = Uri.tryParse(value);
    if (uri == null || !uri.hasScheme || !uri.hasAuthority) {
      return 'Please enter a valid URL';
    }
    if (_isTestObserverIssueUrl(uri) && !_isValidIssuePage(uri)) {
      return 'Invalid Test Observer issue URL, expected: ${Uri.base.origin}/#/issues/<id>';
    }
    return null;
  }

  bool _isTestObserverIssueUrl(Uri uri) {
    return uri.origin == Uri.base.origin;
  }

  bool _isValidIssuePage(Uri uri) {
    return AppRoutes.isIssuePage(_extractRouteUri(uri));
  }

  Future<int> _getOrCreateIssueId(String url, WidgetRef ref) async {
    final uri = Uri.parse(url);
    if (_isTestObserverIssueUrl(uri)) {
      return AppRoutes.issueIdFromUri(_extractRouteUri(uri));
    } else {
      final issue =
          await ref.read(issuesProvider.notifier).createIssue(url: url);
      return issue.id;
    }
  }

  bool _isIssueAlreadyAttached(List issueAttachments, int issueId) {
    return issueAttachments
        .map((attachment) => attachment.issue.id)
        .contains(issueId);
  }

  Future<void> _attachIssue(
    BuildContext context,
    WidgetRef ref,
    List issueAttachments,
    int issueId,
  ) async {
    final issueAlreadyAttached =
        _isIssueAlreadyAttached(issueAttachments, issueId);
    await ref
        .read(testResultsProvider(widget.testExecutionId).notifier)
        .attachIssueToTestResult(widget.testResultId, issueId);
    if (!context.mounted) return;
    if (issueAlreadyAttached) {
      showNotification(context, 'Note: Issue already attached.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final buttonFontStyle = Theme.of(context).textTheme.labelLarge;
    final testResult = ref
        .watch(
          testResultsProvider(widget.testExecutionId).select(
            (value) => value.whenData(
              (results) => results
                  .firstWhere((result) => result.id == widget.testResultId),
            ),
          ),
        )
        .value;
    final issueAttachments = testResult?.issueAttachments ?? [];

    return Form(
      key: formKey,
      child: SizedBox(
        width: Spacing.formWidth,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Attach Issue', style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: Spacing.level4),
            Flexible(
              child: ConstrainedBox(
                constraints: BoxConstraints(
                  maxHeight: MediaQuery.of(context).size.height * 0.6,
                ),
                child: SingleChildScrollView(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      VanillaTextInput(
                        key: const Key('attachIssueFormUrlInput'),
                        label:
                            'Test Observer issue URL or external URL (GitHub, Jira, Launchpad)',
                        controller: urlController,
                        validator: (value) => _validateUrl(value),
                      ),
                      const SizedBox(height: Spacing.level3),
                      Row(
                        children: [
                          Checkbox(
                            value: _createAttachmentRule,
                            onChanged: (checked) {
                              setState(() {
                                _createAttachmentRule = checked ?? false;
                              });
                            },
                          ),
                          const SizedBox(width: 8),
                          const Text('Create attachment rule'),
                        ],
                      ),
                      if (_createAttachmentRule)
                        _CreateAttachmentRuleSection(
                          artefactId: widget.artefactId,
                          testResult: testResult,
                          testExecutionId: widget.testExecutionId,
                          selectedAttachmentRuleFilters:
                              _selectedAttachmentRuleFilters,
                          onChanged: (filters) {
                            setState(() {
                              _selectedAttachmentRuleFilters = filters;
                            });
                          },
                        ),
                    ],
                  ),
                ),
              ),
            ),
            Row(
              children: [
                TextButton(
                  onPressed: () => context.pop(),
                  child: Text(
                    'cancel',
                    style: buttonFontStyle?.apply(color: Colors.grey),
                  ),
                ),
                const Spacer(),
                TextButton(
                  key: const Key('attachIssueFormSubmitButton'),
                  onPressed: () async {
                    if (formKey.currentState?.validate() != true) return;
                    final url = urlController.text.trim();
                    final issueId = await _getOrCreateIssueId(url, ref);
                    if (!context.mounted) return;
                    await _attachIssue(context, ref, issueAttachments, issueId);
                    if (!context.mounted) return;
                    Navigator.of(context).pop();
                  },
                  child: Text(
                    'attach',
                    style: buttonFontStyle?.apply(color: Colors.black),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

void showAttachIssueDialog({
  required BuildContext context,
  required int testExecutionId,
  required int testResultId,
  required int artefactId,
}) =>
    showDialog(
      context: context,
      builder: (_) => Dialog(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: _AttachIssueForm(
            testExecutionId: testExecutionId,
            testResultId: testResultId,
            artefactId: artefactId,
          ),
        ),
      ),
    );

class _CreateAttachmentRuleSection extends ConsumerWidget {
  const _CreateAttachmentRuleSection({
    required this.artefactId,
    required this.testResult,
    required this.testExecutionId,
    required this.selectedAttachmentRuleFilters,
    required this.onChanged,
  });

  final int artefactId;
  final TestResult? testResult;
  final int testExecutionId;
  final AttachmentRuleFilters selectedAttachmentRuleFilters;
  final ValueChanged<AttachmentRuleFilters> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefact = ref.read(artefactProvider(artefactId)).value;
    final familyName = artefact?.family ?? '';
    final templateId = testResult?.templateId ?? '';
    final testCaseName = testResult?.name ?? '';
    final testExecution = ref
        .read(
          artefactBuildsProvider(artefactId).select(
            (value) => value.whenData(
              (builds) =>
                  builds.expand((build) => build.testExecutions).firstWhere(
                        (te) => te.id == testExecutionId,
                      ),
            ),
          ),
        )
        .value;
    final executionMetadata =
        testExecution?.executionMetadata ?? ExecutionMetadata();
    final filters = AttachmentRuleFilters(
      families: familyName.isNotEmpty ? [familyName] : [],
      testCaseNames: testCaseName.isNotEmpty ? [testCaseName] : [],
      templateIds: templateId.isNotEmpty ? [templateId] : [],
      executionMetadata: executionMetadata,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Attachment Rule Filters',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: Spacing.level3),
        AttachmentRuleFiltersWidget(
          filters: filters,
          editable: true,
          initialSelectedFilters: selectedAttachmentRuleFilters,
          onChanged: onChanged,
        ),
        const SizedBox(height: Spacing.level3),
        Text(
          'Attach to existing test results',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        _BulkAttachIssueOption(
          title: 'Older test results',
          initialValue: false,
          testResultsFilters:
              selectedAttachmentRuleFilters.toTestResultsFilters().copyWith(
                    untilDate: testResult?.createdAt,
                  ),
          loadNumberResults: selectedAttachmentRuleFilters.hasFilters,
          // onChanged: null,
        ),
        _BulkAttachIssueOption(
          title: 'Newer test results',
          initialValue: false,
          testResultsFilters:
              selectedAttachmentRuleFilters.toTestResultsFilters().copyWith(
                    fromDate: testResult?.createdAt,
                  ),
          loadNumberResults: selectedAttachmentRuleFilters.hasFilters,
          // onChanged: null,
        ),
      ],
    );
  }
}

class _BulkAttachIssueOption extends ConsumerWidget {
  const _BulkAttachIssueOption({
    required this.title,
    required this.initialValue,
    required this.testResultsFilters,
    this.loadNumberResults = false,
    // required this.onChanged,
  });

  final String title;
  final bool initialValue;
  final TestResultsFilters testResultsFilters;
  final bool loadNumberResults;
  // final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final matchingTestResults = loadNumberResults
        ? ref.watch(
            testResultsSearchProvider(testResultsFilters.copyWith(limit: 0)))
        : null;
    return CheckboxListTile(
      title: Row(
        spacing: Spacing.level3,
        children: [
          Text(title),
          if (loadNumberResults)
            matchingTestResults!.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: YaruCircularProgressIndicator(),
                  )
                : InlineUrlText(
                    url: '/#${testResultsFilters.toTestResultsUri()}',
                    urlText:
                        'Matches ${matchingTestResults.value?.count ?? 0} test results',
                    fontStyle: DefaultTextStyle.of(context).style.apply(
                          color: Theme.of(context).colorScheme.primary,
                          fontStyle: FontStyle.italic,
                          decoration: TextDecoration.none,
                        ),
                  ),
        ],
      ),
      value: initialValue,
      onChanged: null,
    );
  }
}
