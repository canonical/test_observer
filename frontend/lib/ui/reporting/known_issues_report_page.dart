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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../providers/reports.dart';
import '../spacing.dart';
import '../common/error_display.dart';
import '../common/io_log_viewer.dart';

class KnownIssuesReportPage extends ConsumerStatefulWidget {
  const KnownIssuesReportPage({super.key});

  @override
  ConsumerState<KnownIssuesReportPage> createState() =>
      _KnownIssuesReportPageState();
}

class _KnownIssuesReportPageState extends ConsumerState<KnownIssuesReportPage> {
  DateRange? _selectedDateRange;

  // Sorting states for Known Issues table
  int? _knownIssuesSortColumnIndex;
  bool _knownIssuesSortAscending = true;
  String _knownIssuesFilterText = '';

  // Filter to hide closed issues
  bool _hideClosedIssues = true;

  // Selected family types for filtering
  Set<String> _selectedFamilies = {'snap', 'deb'};

  // Track expanded issues
  final Set<int> _expandedIssues = <int>{};

  // Track if all issues are expanded
  bool _allIssuesExpanded = false;

  // Track expanded environments per artefact (issue_id -> artefact_id -> expanded)
  final Map<int, Set<int>> _expandedEnvironments = <int, Set<int>>{};

  // Track expanded success/failure environment sections per artefact (issue_id -> artefact_id -> {'success': bool, 'failure': bool})
  final Map<int, Map<int, Map<String, bool>>> _expandedEnvironmentSections =
      <int, Map<int, Map<String, bool>>>{};

  // Track IO log visibility per environment (issue_id -> artefact_id -> environment_name -> bool)
  final Map<int, Map<int, Map<String, bool>>> _ioLogVisibility =
      <int, Map<int, Map<String, bool>>>{};

  // Track expanded state for issue group sections
  bool _testDefinitionIssuesExpanded = true;
  bool _platformIssuesExpanded = true;

  // Helper function to categorize issues
  String _categorizeIssue(Map<String, dynamic> issue) {
    final url = issue['url']?.toString() ?? '';
    final description = issue['description']?.toString() ?? '';

    // Check for GitHub issues to canonical/checkbox repo
    if (url.contains('github.com/canonical/checkbox')) {
      return 'test_definition';
    }

    // Check for Jira issues with C3- or RTW- prefix in description
    if (description.startsWith('C3-') || description.startsWith('RTW-')) {
      return 'test_definition';
    }

    // Check for Jira issues with C3- or RTW- prefix in URL
    if (url.contains('/C3-') || url.contains('/RTW-')) {
      return 'test_definition';
    }

    return 'platform';
  }

  // Helper function to format error messages for users
  String _formatErrorMessage(dynamic error) {
    final errorStr = error.toString();

    // Handle common network errors
    if (errorStr.contains('XMLHttpRequest') ||
        errorStr.contains('connection error')) {
      return 'Unable to connect to the server. Please check your connection and try again.';
    }

    // Handle timeout errors
    if (errorStr.contains('timeout')) {
      return 'The request took too long. Please try again.';
    }

    // Handle 404 errors
    if (errorStr.contains('404')) {
      return 'The requested data was not found.';
    }

    // Handle 500 errors
    if (errorStr.contains('500') ||
        errorStr.contains('Internal Server Error')) {
      return 'Server error occurred. Please try again later.';
    }

    // Handle authentication errors
    if (errorStr.contains('401') || errorStr.contains('403')) {
      return 'Access denied. Please check your permissions.';
    }

    // Default message for other errors
    return 'An error occurred while loading data. Please try again.';
  }

  @override
  void initState() {
    super.initState();
    // Set default date range to Last 180 days
    final now = DateTime.now();
    _selectedDateRange = DateRange(
      startDate: now.subtract(const Duration(days: 180)),
      endDate: now,
    );
  }

  @override
  Widget build(BuildContext context) {
    final knownIssuesReportAsync = ref.watch(
      knownIssuesReportProvider(_selectedDateRange),
    );

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: Spacing.level5),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Test Case Issues',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              Row(
                children: [
                  _buildDateRangeSelector(),
                  const SizedBox(width: Spacing.level3),
                  _buildFilterTextField(
                    hintText: 'Filter issues...',
                    value: _knownIssuesFilterText,
                    onChanged: (value) {
                      setState(() {
                        _knownIssuesFilterText = value;
                      });
                    },
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: SingleChildScrollView(
              child: _buildKnownIssuesSection(knownIssuesReportAsync),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterTextField({
    required String hintText,
    required String value,
    required ValueChanged<String> onChanged,
  }) {
    return SizedBox(
      width: 300,
      child: TextField(
        decoration: InputDecoration(
          hintText: hintText,
          prefixIcon: const Icon(Icons.search),
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 12,
            vertical: 8,
          ),
        ),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildKnownIssuesSection(
    AsyncValue<Map<String, dynamic>> knownIssuesReportAsync,
  ) {
    return knownIssuesReportAsync.when(
      data: (data) => _buildKnownIssuesContent(data),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            const Text('Failed to load known issues data'),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: () => showErrorDialog(
                context,
                error,
                title: 'Known Issues Error',
                onRetry: () => ref.invalidate(knownIssuesReportProvider),
              ),
              icon: const Icon(Icons.info),
              label: const Text('View Details'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKnownIssuesContent(Map<String, dynamic> data) {
    var issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No known issues found'),
        ),
      );
    }

    // Apply filtering
    if (_knownIssuesFilterText.isNotEmpty) {
      final filterLower = _knownIssuesFilterText.toLowerCase();
      issues = issues.where((issue) {
        return (issue['template_id']?.toString().toLowerCase().contains(
                  filterLower,
                ) ??
                false) ||
            (issue['case_name']?.toString().toLowerCase().contains(
                  filterLower,
                ) ??
                false) ||
            (issue['description']?.toString().toLowerCase().contains(
                  filterLower,
                ) ??
                false) ||
            (issue['url']?.toString().toLowerCase().contains(filterLower) ??
                false) ||
            (issue['issue_status']?.toString().toLowerCase().contains(
                  filterLower,
                ) ??
                false);
      }).toList();
    }

    // Apply closed issues filter
    if (_hideClosedIssues) {
      issues = issues.where((issue) {
        final status = issue['issue_status']?.toString().toUpperCase();
        return status != 'CLOSED';
      }).toList();
    }

    // Apply sorting
    if (_knownIssuesSortColumnIndex != null) {
      issues.sort((a, b) {
        dynamic aValue, bValue;
        switch (_knownIssuesSortColumnIndex) {
          case 0: // Issue (description)
            aValue = a['description'] ?? '';
            bValue = b['description'] ?? '';
            break;
          case 1: // Test Case
            aValue = (a['template_id']?.isNotEmpty == true)
                ? a['template_id']
                : a['case_name'] ?? '';
            bValue = (b['template_id']?.isNotEmpty == true)
                ? b['template_id']
                : b['case_name'] ?? '';
            break;
          case 2: // Status
            aValue = a['issue_status'] ?? 'UNKNOWN';
            bValue = b['issue_status'] ?? 'UNKNOWN';
            break;
          case 3: // Failure combinations count
            aValue = a['failure_combinations_count'] ?? 0;
            bValue = b['failure_combinations_count'] ?? 0;
            break;
          case 4: // Updated
            aValue = DateTime.parse(
              a['updated_at'] ?? DateTime.now().toIso8601String(),
            );
            bValue = DateTime.parse(
              b['updated_at'] ?? DateTime.now().toIso8601String(),
            );
            break;
          default:
            return 0;
        }

        final comparison = aValue.compareTo(bValue);
        return _knownIssuesSortAscending ? comparison : -comparison;
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text(
                  'Total Issues: $totalCount (Showing ${issues.length})',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                if (issues.isNotEmpty) ...[
                  const SizedBox(width: 12),
                  TextButton.icon(
                    onPressed: () {
                      setState(() {
                        _allIssuesExpanded = !_allIssuesExpanded;
                        if (_allIssuesExpanded) {
                          // Expand all issues
                          for (final issue in issues) {
                            _expandedIssues.add(issue['id'] as int);
                          }
                        } else {
                          // Collapse all issues
                          _expandedIssues.clear();
                        }
                      });
                    },
                    icon: Icon(
                      _allIssuesExpanded
                          ? Icons.expand_less
                          : Icons.expand_more,
                      size: 18,
                    ),
                    label: Text(
                      _allIssuesExpanded ? 'Collapse All' : 'Expand All',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      minimumSize: Size.zero,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  ),
                ],
              ],
            ),
            Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Checkbox(
                  value: _hideClosedIssues,
                  onChanged: (value) {
                    setState(() {
                      _hideClosedIssues = value ?? false;
                    });
                  },
                ),
                const Text('Hide closed issues'),
              ],
            ),
          ],
        ),
        const SizedBox(height: Spacing.level3),

        // Group issues by category
        ..._buildGroupedIssues(issues),
      ],
    );
  }

  List<Widget> _buildGroupedIssues(List<dynamic> issues) {
    // Group issues by category
    final testDefinitionIssues = <Map<String, dynamic>>[];
    final platformIssues = <Map<String, dynamic>>[];

    for (final issue in issues) {
      if (_categorizeIssue(issue) == 'test_definition') {
        testDefinitionIssues.add(issue);
      } else {
        platformIssues.add(issue);
      }
    }

    final widgets = <Widget>[];

    // Test Definition Related Issues
    if (testDefinitionIssues.isNotEmpty) {
      widgets.addAll([
        _buildGroupHeader(
          'Test Definition Issues',
          testDefinitionIssues.length,
          Icons.bug_report,
          _testDefinitionIssuesExpanded,
          () {
            setState(() {
              _testDefinitionIssuesExpanded = !_testDefinitionIssuesExpanded;
            });
          },
        ),
        if (_testDefinitionIssuesExpanded) ...[
          const SizedBox(height: Spacing.level2),
          _buildIssuesTable(testDefinitionIssues),
        ],
        const SizedBox(height: Spacing.level4),
      ]);
    }

    // Known Platform Issues
    if (platformIssues.isNotEmpty) {
      widgets.addAll([
        _buildGroupHeader(
          'Known Platform Issues',
          platformIssues.length,
          Icons.error_outline,
          _platformIssuesExpanded,
          () {
            setState(() {
              _platformIssuesExpanded = !_platformIssuesExpanded;
            });
          },
        ),
        if (_platformIssuesExpanded) ...[
          const SizedBox(height: Spacing.level2),
          _buildIssuesTable(platformIssues),
        ],
      ]);
    }

    return widgets;
  }

  Widget _buildGroupHeader(String title, int count, IconData icon, bool isExpanded, VoidCallback onToggle) {
    return InkWell(
      onTap: onToggle,
      borderRadius: BorderRadius.circular(6),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.surfaceContainerHigh,
          borderRadius: BorderRadius.circular(6),
          border: Border.all(color: Theme.of(context).dividerColor),
        ),
        child: Row(
          children: [
            Icon(icon, size: 20, color: Theme.of(context).colorScheme.primary),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.w600,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                count.toString(),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Icon(
              isExpanded ? Icons.expand_less : Icons.expand_more,
              size: 20,
              color: Theme.of(context).colorScheme.primary,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildIssuesTable(List<dynamic> issues) {
    return Column(
      children: [
        // Table header
        Container(
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.surfaceContainerHighest,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
          ),
          child: Row(
            children: [
              const SizedBox(width: 24), // Space for expand icon
              Expanded(flex: 2, child: _buildSortableHeader('Issue', 0)),
              Expanded(flex: 1, child: _buildSortableHeader('Test Case', 1)),
              SizedBox(
                width: 100,
                child: Align(
                  alignment: Alignment.center,
                  child: _buildSortableHeader('Status', 2),
                ),
              ),
              SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.center,
                  child: Tooltip(
                    message:
                        'Number of (artefact × environment) combinations\nwhere a test case linked to this issue has failed',
                    child: _buildSortableHeader('Failed', 3),
                  ),
                ),
              ),
              SizedBox(
                width: 100,
                child: Align(
                  alignment: Alignment.center,
                  child: _buildSortableHeader('Updated', 4),
                ),
              ),
            ],
          ),
        ),
        // Table rows
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Theme.of(context).dividerColor),
            borderRadius: const BorderRadius.vertical(
              bottom: Radius.circular(8),
            ),
          ),
          child: Column(
            children: issues.map<Widget>((issue) {
              final issueId = issue['id'] as int;
              final isExpanded = _expandedIssues.contains(issueId);
              return _buildIssueRow(issue, isExpanded);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildIssueRow(Map<String, dynamic> issue, bool isExpanded) {
    final issueId = issue['id'] as int;
    final description = issue['description'] ?? 'No description';
    final testCase = (issue['template_id']?.isNotEmpty == true)
        ? issue['template_id']
        : issue['case_name'] ?? 'Unknown';
    final updatedAt = DateTime.parse(issue['updated_at']);

    return Column(
      children: [
        InkWell(
          onTap: () {
            setState(() {
              if (isExpanded) {
                _expandedIssues.remove(issueId);
              } else {
                _expandedIssues.add(issueId);
              }
            });
          },
          child: Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            decoration: BoxDecoration(
              border: Border(
                bottom: BorderSide(color: Theme.of(context).dividerColor),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 20,
                ),
                const SizedBox(width: 4),
                Expanded(
                  flex: 2,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        description,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          fontWeight: FontWeight.w500,
                        ),
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      if (issue['url']?.isNotEmpty == true) ...[
                        const SizedBox(height: 2),
                        GestureDetector(
                          onTap: () => _launchUrl(issue['url']),
                          child: Text(
                            issue['url'],
                            style: Theme.of(context).textTheme.bodySmall
                                ?.copyWith(
                                  color: Theme.of(context).colorScheme.primary,
                                  decoration: TextDecoration.underline,
                                ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ],
                  ),
                ),
                Expanded(
                  flex: 1,
                  child: Text(
                    testCase,
                    style: Theme.of(context).textTheme.bodyMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                SizedBox(
                  width: 100,
                  child: Center(child: _buildStatusChip(issue['issue_status'])),
                ),
                SizedBox(
                  width: 80,
                  child: Center(
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.errorContainer,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '${issue['failure_combinations_count'] ?? 0}',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ),
                ),
                SizedBox(
                  width: 100,
                  child: Center(
                    child: Text(
                      _formatDate(updatedAt),
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        if (isExpanded) _buildExpandedContent(issueId),
      ],
    );
  }

  Widget _buildExpandedContent(int issueId) {
    final affectedArtefactsAsync = ref.watch(
      affectedArtefactsProvider(issueId),
    );

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(
          context,
        ).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Associated Artefacts',
            style: Theme.of(
              context,
            ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 8),
          affectedArtefactsAsync.when(
            data: (data) {
              // Handle both old array format and new object format for backward compatibility
              if (data is List) {
                // Old format - treat all as mixed artefacts
                if (data.isEmpty) {
                  return const Text(
                    'No associated artefacts found for this issue.',
                  );
                }
                return Column(
                  children: data.map<Widget>((artefact) {
                    final artefactId = artefact['id'] as int;
                    final issueIdForEnv = issueId; // Use the current issue ID
                    final isEnvExpanded =
                        _expandedEnvironments[issueIdForEnv]?.contains(
                          artefactId,
                        ) ??
                        false;
                    final environments =
                        artefact['environments'] as List? ?? [];
                    final envCount =
                        artefact['environment_count'] as int? ??
                        environments.length;

                    return Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Theme.of(context).colorScheme.surface,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: Theme.of(context).dividerColor,
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(
                                Icons.inventory,
                                size: 16,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                              const SizedBox(width: 4),
                              Expanded(
                                child: Text(
                                  '${artefact['name']} ${artefact['version']}',
                                  style: Theme.of(context).textTheme.bodySmall
                                      ?.copyWith(fontWeight: FontWeight.w500),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 6,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.secondaryContainer,
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  artefact['family'].toString().toUpperCase(),
                                  style: TextStyle(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.onSecondaryContainer,
                                    fontSize: 10,
                                    fontWeight: FontWeight.w500,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Row(
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    if (envCount > 0) ...[
                                      InkWell(
                                        onTap: environments.isNotEmpty
                                            ? () {
                                                setState(() {
                                                  _expandedEnvironments
                                                      .putIfAbsent(
                                                        issueIdForEnv,
                                                        () => <int>{},
                                                      );
                                                  if (isEnvExpanded) {
                                                    _expandedEnvironments[issueIdForEnv]!
                                                        .remove(artefactId);
                                                  } else {
                                                    _expandedEnvironments[issueIdForEnv]!
                                                        .add(artefactId);
                                                  }
                                                });
                                              }
                                            : null,
                                        child: Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            Text(
                                              'Environments: $envCount environment${envCount == 1 ? '' : 's'}',
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .bodySmall
                                                  ?.copyWith(
                                                    color:
                                                        environments.isNotEmpty
                                                        ? Theme.of(
                                                            context,
                                                          ).colorScheme.primary
                                                        : Theme.of(context)
                                                              .colorScheme
                                                              .onSurfaceVariant,
                                                    decoration:
                                                        environments.isNotEmpty
                                                        ? TextDecoration
                                                              .underline
                                                        : null,
                                                  ),
                                            ),
                                            if (environments.isNotEmpty) ...[
                                              const SizedBox(width: 4),
                                              Icon(
                                                isEnvExpanded
                                                    ? Icons.expand_less
                                                    : Icons.expand_more,
                                                size: 16,
                                                color: Theme.of(
                                                  context,
                                                ).colorScheme.primary,
                                              ),
                                            ],
                                          ],
                                        ),
                                      ),
                                      if (isEnvExpanded &&
                                          environments.isNotEmpty) ...[
                                        const SizedBox(height: 4),
                                        Container(
                                          padding: const EdgeInsets.all(8),
                                          decoration: BoxDecoration(
                                            color: Theme.of(context)
                                                .colorScheme
                                                .surfaceContainerHighest
                                                .withValues(alpha: 0.5),
                                            borderRadius: BorderRadius.circular(
                                              4,
                                            ),
                                          ),
                                          child: Wrap(
                                            spacing: 4,
                                            runSpacing: 4,
                                            children: environments.map<Widget>((
                                              env,
                                            ) {
                                              return Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                      horizontal: 6,
                                                      vertical: 2,
                                                    ),
                                                decoration: BoxDecoration(
                                                  color: Theme.of(context)
                                                      .colorScheme
                                                      .primaryContainer,
                                                  borderRadius:
                                                      BorderRadius.circular(4),
                                                ),
                                                child: Text(
                                                  env.toString(),
                                                  style: TextStyle(
                                                    color: Theme.of(context)
                                                        .colorScheme
                                                        .onPrimaryContainer,
                                                    fontSize: 11,
                                                  ),
                                                ),
                                              );
                                            }).toList(),
                                          ),
                                        ),
                                      ],
                                    ] else ...[
                                      Text(
                                        'Environments: 0 environments',
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall
                                            ?.copyWith(
                                              color: Theme.of(
                                                context,
                                              ).colorScheme.onSurfaceVariant,
                                            ),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                              if (artefact['due_date'] != null &&
                                  artefact['due_date'] != 'null') ...[
                                Icon(
                                  Icons.schedule,
                                  size: 14,
                                  color: Theme.of(
                                    context,
                                  ).colorScheme.onSurfaceVariant,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  () {
                                    try {
                                      return 'Due: ${_formatDate(DateTime.parse(artefact['due_date']))}';
                                    } catch (e) {
                                      return 'Due: N/A';
                                    }
                                  }(),
                                  style: Theme.of(context).textTheme.bodySmall
                                      ?.copyWith(
                                        color: Theme.of(
                                          context,
                                        ).colorScheme.onSurfaceVariant,
                                      ),
                                ),
                              ],
                            ],
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                );
              } else if (data is Map) {
                // New format with separated artefacts
                final successOnlyArtefacts =
                    data['success_only_artefacts'] as List? ?? [];
                final artefactsWithFailures =
                    data['artefacts_with_failures'] as List? ?? [];
                final totalArtefacts = data['total_artefacts'] as int? ?? 0;

                if (totalArtefacts == 0) {
                  return const Text(
                    'No associated artefacts found for this issue.',
                  );
                }

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (artefactsWithFailures.isNotEmpty) ...[
                      _buildIssueArtefactSection(
                        'Artefacts where environments failed this test',
                        artefactsWithFailures,
                        issueId,
                        Theme.of(context).colorScheme.surfaceContainerHighest,
                        Theme.of(context).colorScheme.primary,
                      ),
                      const SizedBox(height: 12),
                    ],
                    if (successOnlyArtefacts.isNotEmpty) ...[
                      _buildIssueArtefactSection(
                        'Success-only artefacts',
                        successOnlyArtefacts,
                        issueId,
                        Colors.green.shade100,
                        Colors.green.shade700,
                      ),
                    ],
                  ],
                );
              } else {
                return const Text(
                  'No associated artefacts found for this issue.',
                );
              }
            },
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (error, stack) => Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(
                    Icons.error_outline,
                    color: Theme.of(context).colorScheme.error,
                    size: 20,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _formatErrorMessage(error),
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildIssueArtefactSection(
    String title,
    List artefacts,
    int issueId,
    Color backgroundColor,
    Color borderColor,
  ) {
    // Group artefacts by name
    final groupedArtefacts = <String, List<Map<String, dynamic>>>{};
    for (final artefact in artefacts) {
      final name = artefact['name'] as String;
      groupedArtefacts.putIfAbsent(name, () => []);
      groupedArtefacts[name]!.add(artefact as Map<String, dynamic>);
    }

    // Sort each group by created_at date in descending order (newest first)
    for (final group in groupedArtefacts.values) {
      group.sort((a, b) {
        final aCreatedAt = a['created_at'] as String?;
        final bCreatedAt = b['created_at'] as String?;

        if (aCreatedAt == null && bCreatedAt == null) return 0;
        if (aCreatedAt == null) return 1;
        if (bCreatedAt == null) return -1;

        try {
          final aDate = DateTime.parse(aCreatedAt);
          final bDate = DateTime.parse(bCreatedAt);
          return bDate.compareTo(aDate); // Descending order (newest first)
        } catch (e) {
          return 0;
        }
      });
    }

    // Sort group names alphabetically
    final sortedGroupNames = groupedArtefacts.keys.toList()..sort();

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor.withValues(alpha: 0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '$title (${artefacts.length})',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
              color: borderColor,
            ),
          ),
          const SizedBox(height: 8),
          ...sortedGroupNames.expand((groupName) {
            final groupArtefacts = groupedArtefacts[groupName]!;
            return [
              // Group header
              InkWell(
                onTap: () {
                  final artefact = groupArtefacts.first;
                  final artefactId = artefact['id'] as int;
                  final family = artefact['family'] as String;
                  final path = '/${family}s/$artefactId';
                  context.go(path);
                },
                borderRadius: BorderRadius.circular(4),
                child: Container(
                  margin: const EdgeInsets.only(bottom: 6, top: 6),
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: borderColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                      color: borderColor.withValues(alpha: 0.2),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.inventory_2, size: 16, color: borderColor),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          groupName,
                          style: Theme.of(context).textTheme.bodyMedium
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                                color: borderColor,
                                decoration: TextDecoration.underline,
                              ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 6,
                          vertical: 2,
                        ),
                        decoration: BoxDecoration(
                          color: borderColor.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          '${groupArtefacts.length}',
                          style: TextStyle(
                            color: borderColor,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Icon(Icons.open_in_new, size: 12, color: borderColor),
                    ],
                  ),
                ),
              ),
              // Artefacts in this group
              ...groupArtefacts.map((artefact) {
                final artefactId = artefact['id'] as int;

                return Container(
                  margin: const EdgeInsets.only(bottom: 6, left: 12),
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.surface,
                    borderRadius: BorderRadius.circular(6),
                    border: Border.all(color: Theme.of(context).dividerColor),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.tag,
                            size: 12,
                            color: Theme.of(context).colorScheme.primary,
                          ),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              artefact['version'],
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(fontWeight: FontWeight.w500),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 4,
                              vertical: 1,
                            ),
                            decoration: BoxDecoration(
                              color: Theme.of(
                                context,
                              ).colorScheme.secondaryContainer,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              artefact['family'].toString().toUpperCase(),
                              style: TextStyle(
                                color: Theme.of(
                                  context,
                                ).colorScheme.onSecondaryContainer,
                                fontSize: 9,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          if (artefact['due_date'] != null &&
                              artefact['due_date'] != 'null') ...[
                            const SizedBox(width: 6),
                            Icon(
                              Icons.schedule,
                              size: 12,
                              color: Theme.of(
                                context,
                              ).colorScheme.onSurfaceVariant,
                            ),
                            const SizedBox(width: 2),
                            Text(
                              _formatDate(DateTime.parse(artefact['due_date'])),
                              style: Theme.of(context).textTheme.bodySmall
                                  ?.copyWith(
                                    color: Theme.of(
                                      context,
                                    ).colorScheme.onSurfaceVariant,
                                    fontSize: 10,
                                  ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      _buildEnvironmentSection(artefact, issueId, artefactId),
                    ],
                  ),
                );
              }),
            ];
          }),
        ],
      ),
    );
  }

  Widget _buildEnvironmentSection(
    Map<String, dynamic> artefact,
    int issueId,
    int artefactId,
  ) {
    final environmentDetails = artefact['environment_details'] as List? ?? [];
    final failureEnvironments = artefact['failure_environments'] as List? ?? [];
    final totalEnvCount = artefact['environment_count'] as int? ?? 0;

    if (totalEnvCount == 0) {
      return Text(
        'Environments: 0 environments',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontSize: 11,
        ),
      );
    }

    final isEnvExpanded =
        _expandedEnvironments[issueId]?.contains(artefactId) ??
        (environmentDetails.length < 10);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: environmentDetails.isNotEmpty
              ? () {
                  setState(() {
                    _expandedEnvironments.putIfAbsent(issueId, () => <int>{});
                    if (isEnvExpanded) {
                      _expandedEnvironments[issueId]!.remove(artefactId);
                    } else {
                      _expandedEnvironments[issueId]!.add(artefactId);
                    }
                  });
                }
              : null,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                failureEnvironments.isNotEmpty
                    ? 'Environments: $totalEnvCount environment${totalEnvCount == 1 ? '' : 's'}, ${failureEnvironments.length} failing this test'
                    : 'Environments: $totalEnvCount environment${totalEnvCount == 1 ? '' : 's'}',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: environmentDetails.isNotEmpty
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.onSurfaceVariant,
                  decoration: environmentDetails.isNotEmpty
                      ? TextDecoration.underline
                      : null,
                  fontSize: 11,
                ),
              ),
              if (environmentDetails.isNotEmpty) ...[
                const SizedBox(width: 4),
                Icon(
                  isEnvExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 16,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ],
            ],
          ),
        ),
        if (isEnvExpanded && environmentDetails.isNotEmpty) ...[
          const SizedBox(height: 4),
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Theme.of(
                context,
              ).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: environmentDetails.map<Widget>((envDetail) {
                final envName = envDetail['name'] as String;
                final c3Links = envDetail['c3_links'] as List? ?? [];
                final ioLogs = envDetail['io_logs'] as List? ?? [];
                final hasFailure = envDetail['has_failure'] as bool? ?? false;

                final isIOLogVisible =
                    _ioLogVisibility[issueId]?[artefactId]?[envName] ?? false;

                return _buildEnvironmentCard(
                  envName,
                  c3Links,
                  ioLogs,
                  hasFailure,
                  issueId,
                  artefactId,
                  isIOLogVisible,
                );
              }).toList(),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildEnvironmentSubSection(
    String title,
    List environments,
    int issueId,
    int artefactId,
    String sectionType,
    Color backgroundColor,
    Color textColor,
  ) {
    final isExpanded =
        _expandedEnvironmentSections[issueId]?[artefactId]?[sectionType] ??
        false;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () {
            setState(() {
              _expandedEnvironmentSections.putIfAbsent(
                issueId,
                () => <int, Map<String, bool>>{},
              );
              _expandedEnvironmentSections[issueId]!.putIfAbsent(
                artefactId,
                () => <String, bool>{},
              );
              _expandedEnvironmentSections[issueId]![artefactId]![sectionType] =
                  !isExpanded;
            });
          },
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 3),
            decoration: BoxDecoration(
              color: backgroundColor,
              borderRadius: BorderRadius.circular(4),
              border: Border.all(color: textColor.withValues(alpha: 0.3)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  '$title (${environments.length})',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: textColor,
                    fontSize: 10,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(width: 4),
                Icon(
                  isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 12,
                  color: textColor,
                ),
              ],
            ),
          ),
        ),
        if (isExpanded) ...[
          const SizedBox(height: 2),
          Container(
            padding: const EdgeInsets.all(4),
            decoration: BoxDecoration(
              color: backgroundColor.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(3),
            ),
            child: Wrap(
              spacing: 2,
              runSpacing: 2,
              children: environments.map<Widget>((env) {
                return InkWell(
                  onTap: () => _launchTestflingerUrl(env.toString()),
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 3,
                      vertical: 1,
                    ),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface,
                      borderRadius: BorderRadius.circular(2),
                      border: Border.all(
                        color: textColor.withValues(alpha: 0.2),
                      ),
                    ),
                    child: Text(
                      env.toString(),
                      style: TextStyle(
                        color: textColor,
                        fontSize: 8,
                        fontWeight: FontWeight.w500,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildDateRangeSelector() {
    final now = DateTime.now();

    return PopupMenuButton<String>(
      onSelected: (value) {
        if (value == 'custom') {
          _selectCustomDateRange();
        } else {
          _selectPresetRange(value);
        }
      },
      itemBuilder: (context) {
        final items = <PopupMenuEntry<String>>[
          const PopupMenuItem(
            value: 'today',
            child: Row(
              children: [Icon(Icons.today), SizedBox(width: 8), Text('Today')],
            ),
          ),
          const PopupMenuItem(
            value: 'last7days',
            child: Row(
              children: [
                Icon(Icons.date_range),
                SizedBox(width: 8),
                Text('Last 7 days'),
              ],
            ),
          ),
          const PopupMenuItem(
            value: 'last30days',
            child: Row(
              children: [
                Icon(Icons.date_range),
                SizedBox(width: 8),
                Text('Last 30 days'),
              ],
            ),
          ),
          const PopupMenuItem(
            value: 'last180days',
            child: Row(
              children: [
                Icon(Icons.date_range),
                SizedBox(width: 8),
                Text('Last 180 days'),
              ],
            ),
          ),
          const PopupMenuItem(
            value: 'last365days',
            child: Row(
              children: [
                Icon(Icons.date_range),
                SizedBox(width: 8),
                Text('Last 365 days'),
              ],
            ),
          ),
          const PopupMenuDivider(),
        ];

        // Add last 6 months
        for (int i = 0; i < 6; i++) {
          final month = DateTime(now.year, now.month - i, 1);
          final monthName = _getMonthName(month.month, month.year);
          final value =
              'month-${month.year}-${month.month.toString().padLeft(2, '0')}';

          items.add(
            PopupMenuItem(
              value: value,
              child: Row(
                children: [
                  const Icon(Icons.calendar_today),
                  const SizedBox(width: 8),
                  Text(monthName),
                ],
              ),
            ),
          );
        }

        items.addAll([
          const PopupMenuDivider(),
          const PopupMenuItem(
            value: 'custom',
            child: Row(
              children: [
                Icon(Icons.calendar_month),
                SizedBox(width: 8),
                Text('Custom range...'),
              ],
            ),
          ),
        ]);

        return items;
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: Theme.of(context).dividerColor),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.calendar_today, size: 16),
            const SizedBox(width: 4),
            Text(
              _getPeriodDescription(),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(width: 4),
            const Icon(Icons.arrow_drop_down, size: 16),
          ],
        ),
      ),
    );
  }

  void _selectPresetRange(String value) {
    final now = DateTime.now();
    DateTime? startDate;
    DateTime? endDate = now;

    switch (value) {
      case 'today':
        startDate = DateTime(now.year, now.month, now.day);
        endDate = DateTime(now.year, now.month, now.day, 23, 59, 59);
        break;
      case 'last7days':
        startDate = now.subtract(const Duration(days: 7));
        break;
      case 'last30days':
        startDate = now.subtract(const Duration(days: 30));
        break;
      case 'last180days':
        startDate = now.subtract(const Duration(days: 180));
        break;
      case 'last365days':
        startDate = now.subtract(const Duration(days: 365));
        break;
      default:
        if (value.startsWith('month-')) {
          final parts = value.split('-');
          final year = int.parse(parts[1]);
          final month = int.parse(parts[2]);
          startDate = DateTime(year, month, 1);
          endDate = DateTime(year, month + 1, 0, 23, 59, 59);
        }
    }

    if (startDate != null) {
      setState(() {
        _selectedDateRange = DateRange(startDate: startDate, endDate: endDate);
      });
    }
  }

  Future<void> _selectCustomDateRange() async {
    final DateTimeRange? picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: _selectedDateRange != null
          ? DateTimeRange(
              start:
                  _selectedDateRange!.startDate ??
                  DateTime.now().subtract(const Duration(days: 30)),
              end: _selectedDateRange!.endDate ?? DateTime.now(),
            )
          : DateTimeRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
    );

    if (picked != null) {
      setState(() {
        _selectedDateRange = DateRange(
          startDate: picked.start,
          endDate: DateTime(
            picked.end.year,
            picked.end.month,
            picked.end.day,
            23,
            59,
            59,
          ),
        );
      });
    }
  }

  String _getMonthName(int month, int year) {
    const months = [
      'January',
      'February',
      'March',
      'April',
      'May',
      'June',
      'July',
      'August',
      'September',
      'October',
      'November',
      'December',
    ];
    return '${months[month - 1]} $year';
  }

  String _getPeriodDescription() {
    if (_selectedDateRange == null) return 'period';

    final start = _selectedDateRange!.startDate;
    final end = _selectedDateRange!.endDate;

    if (start == null && end == null) return 'all time';
    if (start == null) return 'up to ${_formatDate(end)}';
    if (end == null) return 'from ${_formatDate(start)}';

    // Check if it's a single day
    if (start.year == end.year &&
        start.month == end.month &&
        start.day == end.day) {
      return _formatDate(start);
    }

    // Check if it's a single month
    if (start.year == end.year &&
        start.month == end.month &&
        start.day == 1 &&
        end.day >= 28) {
      return _getMonthName(start.month, start.year);
    }

    return '${_formatDate(start)} - ${_formatDate(end)}';
  }

  Widget _buildSortableHeader(String title, int columnIndex) {
    final isSelected = _knownIssuesSortColumnIndex == columnIndex;

    return InkWell(
      onTap: () {
        setState(() {
          if (_knownIssuesSortColumnIndex == columnIndex) {
            _knownIssuesSortAscending = !_knownIssuesSortAscending;
          } else {
            _knownIssuesSortColumnIndex = columnIndex;
            _knownIssuesSortAscending = false; // Start with descending order
          }
        });
      },
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Flexible(
            child: Text(
              title,
              style: Theme.of(context).textTheme.titleSmall?.copyWith(
                fontWeight: FontWeight.bold,
                color: isSelected
                    ? Theme.of(context).colorScheme.primary
                    : null,
              ),
              textAlign: columnIndex == 0 ? TextAlign.left : TextAlign.center,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (isSelected) ...[
            const SizedBox(width: 4),
            Icon(
              _knownIssuesSortAscending
                  ? Icons.arrow_upward
                  : Icons.arrow_downward,
              size: 16,
              color: Theme.of(context).colorScheme.primary,
            ),
          ],
        ],
      ),
    );
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Widget _buildStatusChip(String? status) {
    final statusValue = status ?? 'UNKNOWN';
    Color chipColor;
    Color textColor;

    switch (statusValue.toUpperCase()) {
      case 'OPEN':
        chipColor = Theme.of(context).colorScheme.errorContainer;
        textColor = Theme.of(context).colorScheme.onErrorContainer;
        break;
      case 'CLOSED':
        chipColor = Theme.of(context).colorScheme.primaryContainer;
        textColor = Theme.of(context).colorScheme.onPrimaryContainer;
        break;
      case 'UNKNOWN':
      default:
        chipColor = Theme.of(context).colorScheme.surfaceContainerHighest;
        textColor = Theme.of(context).colorScheme.onSurface;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        statusValue,
        style: TextStyle(
          color: textColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Future<void> _launchTestflingerUrl(String environmentName) async {
    final url = 'https://testflinger.canonical.com/queues/$environmentName';
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Widget _buildEnvironmentCard(
    String envName,
    List c3Links,
    List ioLogs,
    bool hasFailure,
    int issueId,
    int artefactId,
    bool isIOLogVisible,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Environment header with controls
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: hasFailure
                  ? Colors.red.shade50
                  : Theme.of(
                      context,
                    ).colorScheme.primaryContainer.withValues(alpha: 0.3),
              borderRadius: BorderRadius.circular(4),
              border: Border.all(
                color: hasFailure
                    ? Colors.red.shade300
                    : Theme.of(
                        context,
                      ).colorScheme.outline.withValues(alpha: 0.3),
              ),
            ),
            child: Row(
              children: [
                // Environment name
                Expanded(
                  child: Text(
                    envName,
                    style: TextStyle(
                      color: hasFailure
                          ? Colors.red.shade800
                          : Theme.of(context).colorScheme.onPrimaryContainer,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),

                // IO Log toggle button
                if (ioLogs.isNotEmpty) ...[
                  IconButton(
                    onPressed: () {
                      setState(() {
                        _ioLogVisibility.putIfAbsent(
                          issueId,
                          () => <int, Map<String, bool>>{},
                        );
                        _ioLogVisibility[issueId]!.putIfAbsent(
                          artefactId,
                          () => <String, bool>{},
                        );
                        _ioLogVisibility[issueId]![artefactId]![envName] =
                            !isIOLogVisible;
                      });
                    },
                    icon: Icon(
                      isIOLogVisible ? Icons.terminal : Icons.terminal_outlined,
                      size: 16,
                    ),
                    tooltip: isIOLogVisible ? 'Hide IO Log' : 'Show IO Log',
                    style: IconButton.styleFrom(
                      minimumSize: const Size(24, 24),
                      padding: const EdgeInsets.all(4),
                    ),
                  ),

                  // IO Log dialog button
                  IconButton(
                    onPressed: () => showIOLogDialog(
                      context,
                      ioLogs.cast<Map<String, dynamic>>(),
                      envName,
                    ),
                    icon: const Icon(Icons.open_in_new, size: 14),
                    tooltip: 'Open IO Log in dialog',
                    style: IconButton.styleFrom(
                      minimumSize: const Size(24, 24),
                      padding: const EdgeInsets.all(4),
                    ),
                  ),
                ],

                // Testflinger link
                IconButton(
                  onPressed: () => _launchTestflingerUrl(envName),
                  icon: const Icon(Icons.device_hub, size: 14),
                  tooltip: 'View in Testflinger',
                  style: IconButton.styleFrom(
                    minimumSize: const Size(24, 24),
                    padding: const EdgeInsets.all(4),
                  ),
                ),
              ],
            ),
          ),

          // C3 Links
          if (c3Links.isNotEmpty) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.surface,
                borderRadius: BorderRadius.circular(4),
                border: Border.all(
                  color: Theme.of(
                    context,
                  ).colorScheme.outline.withValues(alpha: 0.2),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'C3 Submissions (${c3Links.length}):',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontWeight: FontWeight.w500,
                      fontSize: 10,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Wrap(
                    spacing: 4,
                    runSpacing: 2,
                    children: c3Links.map<Widget>((c3Link) {
                      final url = c3Link['url'] as String;
                      final status = c3Link['status'] as String;
                      final testExecutionId =
                          c3Link['test_execution_id'] as int;

                      return InkWell(
                        onTap: () => _launchUrl(url),
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 4,
                            vertical: 2,
                          ),
                          decoration: BoxDecoration(
                            color: status == 'FAILED'
                                ? Colors.red.shade100
                                : Colors.green.shade100,
                            borderRadius: BorderRadius.circular(3),
                            border: Border.all(
                              color: status == 'FAILED'
                                  ? Colors.red.shade300
                                  : Colors.green.shade300,
                              width: 0.5,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                'TE$testExecutionId',
                                style: TextStyle(
                                  fontSize: 9,
                                  fontWeight: FontWeight.bold,
                                  color: status == 'FAILED'
                                      ? Colors.red.shade700
                                      : Colors.green.shade700,
                                ),
                              ),
                              const SizedBox(width: 2),
                              Icon(
                                Icons.launch,
                                size: 8,
                                color: status == 'FAILED'
                                    ? Colors.red.shade600
                                    : Colors.green.shade600,
                              ),
                            ],
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                ],
              ),
            ),
          ],

          // IO Log display (when toggled on)
          if (isIOLogVisible && ioLogs.isNotEmpty) ...[
            const SizedBox(height: 4),
            IOLogViewer(
              ioLogs: ioLogs.cast<Map<String, dynamic>>(),
              environmentName: envName,
            ),
          ],
        ],
      ),
    );
  }
}
