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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:yaru/yaru.dart';

import '../../models/detailed_test_results.dart';
import '../../models/family_name.dart';
import '../../models/issue.dart';
import '../../models/search_page_results.dart';
import '../../providers/api.dart';
import '../date_time.dart';
import '../execution_metadata.dart';
import '../inline_url_text.dart';
import 'search_page_results_navigation.dart';

class SearchPageTestResultDetailsDialog extends ConsumerStatefulWidget {
  const SearchPageTestResultDetailsDialog({super.key, required this.result});

  final SearchPageTableRow result;

  @override
  ConsumerState<SearchPageTestResultDetailsDialog> createState() =>
      _TestResultDetailsDialogState();
}

class _TestResultDetailsDialogState
    extends ConsumerState<SearchPageTestResultDetailsDialog> {
  SearchPageDetailsResponse? _details;
  Object? _error;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    Future<void>.microtask(_loadDetails);
  }

  Future<void> _loadDetails() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final details = await ref
          .read(apiProvider)
          .getSearchPageTestResultDetails(widget.result.testResult.id);
      if (mounted) {
        setState(() {
          _details = details;
          _isLoading = false;
        });
      }
    } catch (error) {
      if (mounted) {
        setState(() {
          _error = error;
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 900, maxHeight: 1000),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _DialogHeader(onClose: () => Navigator.of(context).pop()),
            if (_isLoading)
              const Expanded(
                child: Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 12),
                      Text('Loading test result details…'),
                    ],
                  ),
                ),
              )
            else if (_error != null)
              Expanded(
                child: Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.error_outline,
                          size: 48,
                          color: Colors.red,
                        ),
                        const SizedBox(height: 12),
                        const Text('Error loading test result details'),
                        const SizedBox(height: 8),
                        Text(
                          _error.toString(),
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.red),
                        ),
                        const SizedBox(height: 16),
                        FilledButton.icon(
                          onPressed: _loadDetails,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              )
            else
              Expanded(child: _DialogContent(result: _details!)),
            _DialogFooter(
              onClose: () => Navigator.of(context).pop(),
              result: widget.result,
            ),
          ],
        ),
      ),
    );
  }
}

/// Legacy dialog retained for Issue detail, which still uses the full result API.
class TestResultDetailsDialog extends StatelessWidget {
  const TestResultDetailsDialog({super.key, required this.result});

  final TestResultWithContext result;

  @override
  Widget build(BuildContext context) {
    final tableRow = _legacyTableRow(result);
    return Dialog(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 900, maxHeight: 1000),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _DialogHeader(onClose: () => Navigator.of(context).pop()),
            Expanded(child: _DialogContent(result: _legacyDetails(result))),
            _DialogFooter(
              onClose: () => Navigator.of(context).pop(),
              result: tableRow,
            ),
          ],
        ),
      ),
    );
  }
}

SearchPageTableRow _legacyTableRow(TestResultWithContext result) {
  return SearchPageTableRow(
    testResult: SearchPageTableTestResult(
      id: result.testResult.id,
      name: result.testResult.name,
      category: result.testResult.category,
      createdAt: result.testResult.createdAt,
      templateId: result.testResult.templateId,
      status: result.testResult.status,
    ),
    testExecution: SearchPageTableTestExecution(
      id: result.testExecution.id,
      status: result.testExecution.status,
      environment: SearchPageTableEnvironment(
        name: result.testExecution.environment.name,
      ),
      testPlan: result.testExecution.testPlan,
      executionMetadata: result.testExecution.executionMetadata,
    ),
    artefact: SearchPageTableArtefact(
      id: result.artefact.id,
      name: result.artefact.name,
      version: result.artefact.version,
      track: result.artefact.track,
      family: FamilyName.values.firstWhere(
        (family) => family.name == result.artefact.family,
        orElse: () => FamilyName.values.first,
      ),
    ),
    artefactBuild: SearchPageTableArtefactBuild(
      architecture: result.artefactBuild.architecture,
    ),
  );
}

SearchPageDetailsResponse _legacyDetails(TestResultWithContext result) {
  final tableRow = _legacyTableRow(result);
  return SearchPageDetailsResponse(
    testResult: SearchPageDetailsTestResult(
      id: result.testResult.id,
      name: result.testResult.name,
      category: result.testResult.category,
      templateId: result.testResult.templateId,
      status: result.testResult.status,
      ioLog: result.testResult.ioLog,
      issues:
          result.testResult.issueAttachments
              .map(
                (attachment) => SearchPageDetailsIssue(
                  id: attachment.issue.id,
                  source: attachment.issue.source,
                  project: attachment.issue.project,
                  key: attachment.issue.key,
                  title: attachment.issue.title,
                  status: attachment.issue.status,
                  url: attachment.issue.url,
                ),
              )
              .toList(),
    ),
    testExecution: SearchPageDetailsTestExecution(
      id: result.testExecution.id,
      status: result.testExecution.status,
      environment: tableRow.testExecution.environment,
      testPlan: result.testExecution.testPlan,
      executionMetadata: result.testExecution.executionMetadata,
      createdAt: result.testExecution.createdAt,
    ),
    artefact: SearchPageDetailsArtefact(
      id: tableRow.artefact.id,
      name: tableRow.artefact.name,
      version: tableRow.artefact.version,
      track: tableRow.artefact.track,
      family: tableRow.artefact.family,
    ),
    artefactBuild: tableRow.artefactBuild,
  );
}

class _DialogHeader extends StatelessWidget {
  const _DialogHeader({required this.onClose});

  final VoidCallback onClose;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: YaruColors.orange,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(4),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Colors.white),
          const SizedBox(width: 8),
          const Text(
            'Test Result Details',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.close, color: Colors.white),
            onPressed: onClose,
          ),
        ],
      ),
    );
  }
}

class _DialogContent extends StatelessWidget {
  const _DialogContent({required this.result});

  final SearchPageDetailsResponse result;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _DialogSection(
            title: 'Test Case',
            children: [
              _DetailRow(label: 'Name', value: result.testResult.name),
              _DetailRow(label: 'Category', value: result.testResult.category),
              _DetailRow(
                label: 'Template ID',
                value: result.testResult.templateId,
              ),
              _DetailRow(label: 'Status', value: result.testResult.status.name),
            ],
          ),
          const SizedBox(height: 16),
          _DialogSection(
            title: 'Artefact',
            children: [
              _DetailRow(
                label: 'Family',
                value: result.artefact.family.name.toUpperCase(),
              ),
              _DetailRow(label: 'Name', value: result.artefact.name),
              _DetailRow(label: 'Version', value: result.artefact.version),
              _DetailRow(label: 'Track', value: result.artefact.track),
              _DetailRow(
                label: 'Architecture',
                value: result.artefactBuild.architecture,
              ),
            ],
          ),
          const SizedBox(height: 16),
          _DialogSection(
            title: 'Test Execution',
            children: [
              _DetailRow(
                label: 'Execution ID',
                value: result.testExecution.id.toString(),
              ),
              _DetailRow(
                label: 'Test Plan',
                value: result.testExecution.testPlan,
              ),
              _DetailRow(
                label: 'Environment',
                value: result.testExecution.environment.name,
              ),
              _DetailRow(
                label: 'Status',
                value: result.testExecution.status.name,
              ),
              _DetailRow(
                label: 'Created',
                value: formatDateTime(result.testExecution.createdAt),
              ),
              _DetailRow(
                label: 'Execution Metadata',
                valueWidget: ExecutionMetadataTable(
                  metadata: result.testExecution.executionMetadata,
                ),
              ),
            ],
          ),
          if (result.testResult.issues.isNotEmpty) ...[
            const SizedBox(height: 16),
            _DialogSection(
              title: 'Issues',
              children:
                  result.testResult.issues
                      .map(
                        (issue) => Padding(
                          padding: const EdgeInsets.only(bottom: 8),
                          child: InkWell(
                            borderRadius: BorderRadius.circular(8),
                            onTap:
                                () => launchUrl(
                                  Uri.base.replace(
                                    fragment: '/issues/${issue.id}',
                                  ),
                                  mode: LaunchMode.externalApplication,
                                ),
                            child: Card(
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: _SearchPageIssueWidget(issue: issue),
                              ),
                            ),
                          ),
                        ),
                      )
                      .toList(),
            ),
          ],
          if (result.testResult.ioLog.isNotEmpty) ...[
            const SizedBox(height: 16),
            _DialogSection(
              title: 'IO Log',
              children: [_LogContainer(logContent: result.testResult.ioLog)],
            ),
          ],
        ],
      ),
    );
  }
}

class _SearchPageIssueWidget extends StatelessWidget {
  const _SearchPageIssueWidget({required this.issue});

  final SearchPageDetailsIssue issue;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme.bodyMedium;
    final linkStyle = style?.copyWith(
      decoration: TextDecoration.underline,
      color: Colors.blue,
    );
    final (label, icon, color) = switch (issue.status) {
      IssueStatus.open => ('Open', Icons.adjust, Colors.green),
      IssueStatus.closed => (
        'Closed',
        Icons.check_circle_outline,
        Colors.purple,
      ),
      IssueStatus.unknown => ('Unknown', Icons.help_outline, Colors.grey),
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisSize: MainAxisSize.min,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          spacing: 12,
          children: [
            Text(
              issue.source.name.toUpperCase(),
              style: style?.copyWith(fontWeight: FontWeight.bold),
            ),
            Text(issue.project, style: style?.copyWith(color: Colors.grey)),
            InlineUrlText(
              url: issue.url,
              urlText:
                  issue.source == IssueSource.jira
                      ? '${issue.project}-${issue.key}'
                      : '#${issue.key}',
              fontStyle: linkStyle,
            ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(icon, color: color, size: style?.fontSize ?? 18),
                const SizedBox(width: 6),
                Text(label, style: style),
              ],
            ),
          ],
        ),
        const SizedBox(height: 12),
        Text(
          issue.title.isNotEmpty ? issue.title : '[No title]',
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: Theme.of(context).colorScheme.primary,
          ),
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
        ),
      ],
    );
  }
}

class _DialogFooter extends StatelessWidget {
  const _DialogFooter({required this.onClose, required this.result});

  final VoidCallback onClose;
  final SearchPageTableRow result;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(4),
          bottomRight: Radius.circular(4),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          InkWell(
            onTap: () {
              launchUrl(
                Uri.base.replace(fragment: searchPageRunPath(result)),
                mode: LaunchMode.externalApplication,
              );
            },
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.launch, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text('View Run', style: TextStyle(color: YaruColors.orange)),
                ],
              ),
            ),
          ),
          const SizedBox(width: 4),
          TextButton(onPressed: onClose, child: const Text('Close')),
        ],
      ),
    );
  }
}

class _DialogSection extends StatelessWidget {
  const _DialogSection({required this.title, required this.children});

  final String title;
  final List<Widget> children;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SelectableText(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: YaruColors.orange,
          ),
        ),
        const SizedBox(height: 8),
        ...children,
      ],
    );
  }
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, this.value, this.valueWidget});

  final String label;
  final String? value;
  final Widget? valueWidget;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 200,
            child: SelectableText(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
            ),
          ),
          Expanded(
            child:
                valueWidget ??
                SelectableText(
                  value ?? 'N/A',
                  style: const TextStyle(color: Colors.black),
                ),
          ),
        ],
      ),
    );
  }
}

class _LogContainer extends StatelessWidget {
  const _LogContainer({required this.logContent});

  final String logContent;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: SelectableText(
        logContent,
        style: const TextStyle(fontFamily: 'UbuntuMono', fontSize: 12),
      ),
    );
  }
}
