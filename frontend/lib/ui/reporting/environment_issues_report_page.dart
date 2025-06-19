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
import 'package:url_launcher/url_launcher.dart';
import 'package:intl/intl.dart';
import 'package:go_router/go_router.dart';

import '../../providers/reports.dart';
import '../spacing.dart';
import '../common/error_display.dart';

class EnvironmentIssuesReportPage extends ConsumerStatefulWidget {
  const EnvironmentIssuesReportPage({super.key});

  @override
  ConsumerState<EnvironmentIssuesReportPage> createState() => _EnvironmentIssuesReportPageState();
}

class _EnvironmentIssuesReportPageState extends ConsumerState<EnvironmentIssuesReportPage> {
  // Date range state
  DateRange? _selectedDateRange;
  
  // Sorting states for Environment Issues table
  int? _environmentIssuesSortColumnIndex;
  bool _environmentIssuesSortAscending = true;
  String _environmentIssuesFilterText = '';
  
  // Filter to hide issues with no affected artifacts
  bool _hideUnaffectedIssues = false;
  
  // Track expanded issues
  final Set<int> _expandedIssues = <int>{};
  
  // Track if all issues are expanded
  bool _allIssuesExpanded = false;
  
  // Track expanded environments per artefact (issue_id -> artefact_id -> expanded)
  final Map<int, Set<int>> _expandedEnvironments = <int, Set<int>>{};
  
  // Track expanded state for issue group sections
  bool _confirmedIssuesExpanded = true;
  bool _unconfirmedIssuesExpanded = true;
  
  @override
  void initState() {
    super.initState();
    // Set default date range to Last 30 days
    final now = DateTime.now();
    _selectedDateRange = DateRange(
      startDate: now.subtract(const Duration(days: 30)),
      endDate: now,
    );
  }

  @override
  Widget build(BuildContext context) {
    final environmentIssuesReportAsync = ref.watch(environmentIssuesReportProvider(_selectedDateRange));

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
                'Environment Issues',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              Row(
                children: [
                  _buildDateRangeSelector(),
                  const SizedBox(width: Spacing.level3),
                  _buildFilterTextField(
                    hintText: 'Filter issues...',
                    value: _environmentIssuesFilterText,
                    onChanged: (value) {
                      setState(() {
                        _environmentIssuesFilterText = value;
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
              child: _buildEnvironmentIssuesSection(environmentIssuesReportAsync),
            ),
          ),
        ],
      ),
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
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildEnvironmentIssuesSection(AsyncValue<Map<String, dynamic>> environmentIssuesReportAsync) {
    return environmentIssuesReportAsync.when(
      data: (data) => _buildEnvironmentIssuesContent(data),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            const Text('Failed to load environment issues data'),
            const SizedBox(height: 8),
            ElevatedButton.icon(
              onPressed: () => showErrorDialog(
                context,
                error,
                title: 'Environment Issues Error',
                onRetry: () => ref.invalidate(environmentIssuesReportProvider),
              ),
              icon: const Icon(Icons.info),
              label: const Text('View Details'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEnvironmentIssuesContent(Map<String, dynamic> data) {
    var issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No environment issues found'),
        ),
      );
    }

    // Apply filtering
    if (_environmentIssuesFilterText.isNotEmpty) {
      final filterLower = _environmentIssuesFilterText.toLowerCase();
      issues = issues.where((issue) {
        return (issue['environment_name']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['description']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['url']?.toString().toLowerCase().contains(filterLower) ?? false) ||
               (issue['issue_status']?.toString().toLowerCase().contains(filterLower) ?? false);
      }).toList();
    }

    // Apply unaffected issues filter
    if (_hideUnaffectedIssues) {
      issues = issues.where((issue) {
        final affectedCount = issue['affected_artifacts_count'] ?? 0;
        return affectedCount > 0;
      }).toList();
    }

    // Apply sorting
    if (_environmentIssuesSortColumnIndex != null) {
      issues.sort((a, b) {
        dynamic aValue, bValue;
        switch (_environmentIssuesSortColumnIndex) {
          case 0: // Issue (description)
            aValue = a['description'] ?? '';
            bValue = b['description'] ?? '';
            break;
          case 1: // Environment
            aValue = a['environment_name'] ?? '';
            bValue = b['environment_name'] ?? '';
            break;
          case 2: // Status
            aValue = a['is_confirmed'] == true ? 'Confirmed' : 'Unconfirmed';
            bValue = b['is_confirmed'] == true ? 'Confirmed' : 'Unconfirmed';
            break;
          case 3: // Affected artifacts count
            aValue = a['affected_artifacts_count'] ?? 0;
            bValue = b['affected_artifacts_count'] ?? 0;
            break;
          default:
            return 0;
        }

        final comparison = aValue.compareTo(bValue);
        return _environmentIssuesSortAscending ? comparison : -comparison;
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
                  value: _hideUnaffectedIssues,
                  onChanged: (value) {
                    setState(() {
                      _hideUnaffectedIssues = value ?? false;
                    });
                  },
                ),
                const Text('Hide unaffected issues'),
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
    // Group issues by confirmation status
    final confirmedIssues = <Map<String, dynamic>>[];
    final unconfirmedIssues = <Map<String, dynamic>>[];

    for (final issue in issues) {
      if (issue['is_confirmed'] == true) {
        confirmedIssues.add(issue);
      } else {
        unconfirmedIssues.add(issue);
      }
    }

    final widgets = <Widget>[];

    // Confirmed Environment Issues
    if (confirmedIssues.isNotEmpty) {
      widgets.addAll([
        _buildGroupHeader(
          'Confirmed Environment Issues',
          confirmedIssues.length,
          Icons.check_circle,
          _confirmedIssuesExpanded,
          () {
            setState(() {
              _confirmedIssuesExpanded = !_confirmedIssuesExpanded;
            });
          },
        ),
        if (_confirmedIssuesExpanded) ...[
          const SizedBox(height: Spacing.level2),
          _buildIssuesTable(confirmedIssues),
        ],
        const SizedBox(height: Spacing.level4),
      ]);
    }

    // Unconfirmed Environment Issues
    if (unconfirmedIssues.isNotEmpty) {
      widgets.addAll([
        _buildGroupHeader(
          'Unconfirmed Environment Issues',
          unconfirmedIssues.length,
          Icons.help_outline,
          _unconfirmedIssuesExpanded,
          () {
            setState(() {
              _unconfirmedIssuesExpanded = !_unconfirmedIssuesExpanded;
            });
          },
        ),
        if (_unconfirmedIssuesExpanded) ...[
          const SizedBox(height: Spacing.level2),
          _buildIssuesTable(unconfirmedIssues),
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
              Expanded(flex: 1, child: _buildSortableHeader('Environment', 1)),
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
                        'Number of artifacts affected by failures\nin this environment during the selected time range',
                    child: _buildSortableHeader('Affected', 3),
                  ),
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
    final environmentName = issue['environment_name'] ?? 'Unknown';
    final affectedCount = issue['affected_artifacts_count'] ?? 0;

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
                    environmentName,
                    style: Theme.of(context).textTheme.bodyMedium,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                SizedBox(
                  width: 100,
                  child: Center(child: _buildStatusChip(issue['is_confirmed'])),
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
                        color: affectedCount > 0 
                            ? Theme.of(context).colorScheme.errorContainer
                            : Theme.of(context).colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '$affectedCount',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: affectedCount > 0
                              ? Theme.of(context).colorScheme.onErrorContainer
                              : Theme.of(context).colorScheme.onSurface,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
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
    final params = EnvironmentAffectedArtefactsParams(
      issueId: issueId,
      dateRange: _selectedDateRange,
    );
    
    return Consumer(
      builder: (context, ref, child) {
        final affectedArtefactsAsync = ref.watch(environmentAffectedArtefactsProvider(params));
        
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
                'Affected Artefacts',
                style: Theme.of(
                  context,
                ).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              affectedArtefactsAsync.when(
                data: (data) => _buildAffectedArtefactsList(data),
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
                          'Failed to load affected artefacts: $error',
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
      },
    );
  }

  Widget _buildSortableHeader(String title, int columnIndex) {
    final isSelected = _environmentIssuesSortColumnIndex == columnIndex;

    return InkWell(
      onTap: () {
        setState(() {
          if (_environmentIssuesSortColumnIndex == columnIndex) {
            _environmentIssuesSortAscending = !_environmentIssuesSortAscending;
          } else {
            _environmentIssuesSortColumnIndex = columnIndex;
            _environmentIssuesSortAscending = false; // Start with descending order
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
              _environmentIssuesSortAscending
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

  Widget _buildStatusChip(bool? isConfirmed) {
    final confirmed = isConfirmed ?? false;
    Color chipColor;
    Color textColor;
    String statusText;

    if (confirmed) {
      chipColor = Theme.of(context).colorScheme.primaryContainer;
      textColor = Theme.of(context).colorScheme.onPrimaryContainer;
      statusText = 'Confirmed';
    } else {
      chipColor = Theme.of(context).colorScheme.surfaceContainerHighest;
      textColor = Theme.of(context).colorScheme.onSurface;
      statusText = 'Unconfirmed';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        statusText,
        style: TextStyle(
          color: textColor,
          fontSize: 12,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildAffectedArtefactsList(Map<String, dynamic> data) {
    final artefacts = data['affected_artefacts'] as List<dynamic>? ?? [];
    final totalCount = data['total_artefacts'] ?? 0;
    final environmentName = data['environment_name'] ?? 'Unknown';

    if (artefacts.isEmpty) {
      return Text(
        'No artefacts affected in environment "$environmentName" during the selected time period.',
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
          fontStyle: FontStyle.italic,
        ),
      );
    }

    // For environment issues, all artifacts are "affected" (failed in this environment)
    return _buildEnvironmentArtefactSection(
      'Artefacts affected in environment "$environmentName"',
      artefacts,
      Theme.of(context).colorScheme.surfaceContainerHighest,
      Theme.of(context).colorScheme.primary,
    );
  }

  Widget _buildEnvironmentArtefactSection(
    String title,
    List artefacts,
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
                final artefactId = (artefact['build_id'] as int?) ?? (artefact['id'] as int);

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
                      _buildTestExecutionSection(artefact, artefactId),
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

  Widget _buildTestExecutionSection(
    Map<String, dynamic> artefact,
    int artefactId,
  ) {
    final testExecutionDetails = artefact['test_execution_details'] as List? ?? [];
    final c3Links = artefact['c3_links'] as List? ?? [];
    final ioLogs = artefact['io_logs'] as List? ?? [];
    final failureCount = artefact['failure_count'] as int? ?? 0;

    if (testExecutionDetails.isEmpty) {
      return Text(
        'Test executions: 0 executions',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontSize: 11,
        ),
      );
    }

    final isExpanded =
        _expandedEnvironments[artefactId]?.isNotEmpty ?? (testExecutionDetails.length < 5);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: testExecutionDetails.isNotEmpty
              ? () {
                  setState(() {
                    _expandedEnvironments.putIfAbsent(artefactId, () => <int>{});
                    if (isExpanded) {
                      _expandedEnvironments[artefactId]!.clear();
                    } else {
                      _expandedEnvironments[artefactId]!.add(1); // Dummy value to indicate expanded
                    }
                  });
                }
              : null,
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'Test executions: ${testExecutionDetails.length} execution${testExecutionDetails.length == 1 ? '' : 's'}, $failureCount failed',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: testExecutionDetails.isNotEmpty
                      ? Theme.of(context).colorScheme.primary
                      : Theme.of(context).colorScheme.onSurfaceVariant,
                  decoration: testExecutionDetails.isNotEmpty
                      ? TextDecoration.underline
                      : null,
                  fontSize: 11,
                ),
              ),
              if (testExecutionDetails.isNotEmpty) ...[
                const SizedBox(width: 4),
                Icon(
                  isExpanded ? Icons.expand_less : Icons.expand_more,
                  size: 16,
                  color: Theme.of(context).colorScheme.primary,
                ),
              ],
            ],
          ),
        ),
        if (isExpanded && testExecutionDetails.isNotEmpty) ...[
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
              children: [
                // C3 Links section
                if (c3Links.isNotEmpty) ...[
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
                      final testExecutionId = c3Link['test_execution_id'] as int;

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
                  const SizedBox(height: 8),
                ],
                // Test execution details
                Text(
                  'Test Cases:',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w500,
                    fontSize: 10,
                  ),
                ),
                const SizedBox(height: 4),
                ...testExecutionDetails.map<Widget>((execution) {
                  final testCaseName = execution['test_case_name'] as String? ?? 'Unknown';
                  final status = execution['test_result_status'] as String;
                  final executionId = execution['test_execution_id'] as int;

                  return Container(
                    margin: const EdgeInsets.only(bottom: 2),
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                    decoration: BoxDecoration(
                      color: status == 'FAILED'
                          ? Colors.red.shade50
                          : Colors.green.shade50,
                      borderRadius: BorderRadius.circular(2),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          status == 'FAILED' ? Icons.close : Icons.check,
                          size: 12,
                          color: status == 'FAILED' ? Colors.red : Colors.green,
                        ),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            testCaseName,
                            style: TextStyle(
                              fontSize: 9,
                              color: status == 'FAILED' ? Colors.red.shade700 : Colors.green.shade700,
                            ),
                          ),
                        ),
                        Text(
                          'TE$executionId',
                          style: TextStyle(
                            fontSize: 8,
                            color: Theme.of(context).colorScheme.onSurfaceVariant,
                          ),
                        ),
                      ],
                    ),
                  );
                }).toList(),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}