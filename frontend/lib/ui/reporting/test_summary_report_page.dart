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
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../providers/reports.dart';
import '../spacing.dart';

/// Test Summary Report page with deep linkable date ranges.
/// 
/// Supports the following URL query parameters:
/// - ?date_range=today
/// - ?date_range=last7days
/// - ?date_range=last30days 
/// - ?date_range=last365days
/// - ?date_range=month-YYYY-MM (e.g., month-2025-06 for June 2025)
/// - ?date_range=YYYY-MM-DD--YYYY-MM-DD (custom range)
class TestSummaryReportPage extends ConsumerStatefulWidget {
  const TestSummaryReportPage({super.key});

  @override
  ConsumerState<TestSummaryReportPage> createState() => _TestSummaryReportPageState();
}

class _TestSummaryReportPageState extends ConsumerState<TestSummaryReportPage> {
  DateRange? _selectedDateRange;
  
  // Sorting states for Test Summary table
  int? _testSummarySortColumnIndex;
  bool _testSummarySortAscending = true;
  String _testSummaryFilterText = '';
  
  // Track expanded test cases
  final Set<String> _expandedTestCases = <String>{};
  
  // Cache test identifiers to avoid repeated API calls
  List<String>? _cachedTestIdentifiers;
  List<dynamic>? _cachedSummaryData;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeDateRangeFromUrl();
    });
  }

  void _initializeDateRangeFromUrl() {
    final uri = GoRouterState.of(context).uri;
    final dateRangeParam = uri.queryParameters['date_range'];
    
    if (dateRangeParam != null) {
      final dateRange = _parseDateRangeFromUrl(dateRangeParam);
      if (dateRange != null) {
        setState(() {
          _selectedDateRange = dateRange;
        });
      }
    }
  }

  DateRange? _parseDateRangeFromUrl(String dateRangeParam) {
    try {
      // Handle preset ranges
      if (dateRangeParam == 'today') {
        final now = DateTime.now();
        final today = DateTime(now.year, now.month, now.day);
        return DateRange(startDate: today, endDate: now);
      } else if (dateRangeParam == 'last7days') {
        final now = DateTime.now();
        return DateRange(startDate: now.subtract(const Duration(days: 7)), endDate: now);
      } else if (dateRangeParam == 'last30days') {
        final now = DateTime.now();
        return DateRange(startDate: now.subtract(const Duration(days: 30)), endDate: now);
      } else if (dateRangeParam == 'last365days') {
        final now = DateTime.now();
        return DateRange(startDate: now.subtract(const Duration(days: 365)), endDate: now);
      } else if (dateRangeParam.startsWith('month-')) {
        // Handle month format: "month-YYYY-MM"
        final monthPart = dateRangeParam.substring(6); // Remove "month-"
        final parts = monthPart.split('-');
        if (parts.length == 2) {
          final year = int.tryParse(parts[0]);
          final month = int.tryParse(parts[1]);
          if (year != null && month != null) {
            final startDate = DateTime(year, month, 1);
            final endDate = DateTime(year, month + 1, 0, 23, 59, 59, 999);
            return DateRange(startDate: startDate, endDate: endDate);
          }
        }
      } else if (dateRangeParam.contains('--')) {
        // Handle custom range format: "YYYY-MM-DD--YYYY-MM-DD"
        final parts = dateRangeParam.split('--');
        if (parts.length == 2) {
          final startDate = DateTime.tryParse(parts[0]);
          final endDate = DateTime.tryParse(parts[1]);
          if (startDate != null && endDate != null) {
            return DateRange(startDate: startDate, endDate: endDate);
          }
        }
      }
    } catch (e) {
      // Ignore parsing errors and return null
    }
    return null;
  }

  void _updateUrlWithDateRange(DateRange? dateRange) {
    final currentUri = GoRouterState.of(context).uri;
    final queryParams = Map<String, String>.from(currentUri.queryParameters);
    
    if (dateRange != null) {
      final dateRangeParam = _formatDateRangeForUrl(dateRange);
      queryParams['date_range'] = dateRangeParam;
    } else {
      queryParams.remove('date_range');
    }
    
    final newUri = currentUri.replace(queryParameters: queryParams.isEmpty ? null : queryParams);
    context.go(newUri.toString());
  }

  String _formatDateRangeForUrl(DateRange dateRange) {
    final start = dateRange.startDate;
    final end = dateRange.endDate;
    
    if (start == null || end == null) return '';
    
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    // Check for preset ranges
    if (start.year == today.year && start.month == today.month && start.day == today.day) {
      return 'today';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 7)))) {
      return 'last7days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 30)))) {
      return 'last30days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 365)))) {
      return 'last365days';
    } else if (_isMonthRange(start, end)) {
      // Month format
      return 'month-${start.year}-${start.month.toString().padLeft(2, '0')}';
    } else {
      // Custom range format
      final startStr = '${start.year}-${start.month.toString().padLeft(2, '0')}-${start.day.toString().padLeft(2, '0')}';
      final endStr = '${end.year}-${end.month.toString().padLeft(2, '0')}-${end.day.toString().padLeft(2, '0')}';
      return '$startStr--$endStr';
    }
  }

  bool _isMonthRange(DateTime start, DateTime end) {
    // Check if this is a full month range
    final firstDayOfMonth = DateTime(start.year, start.month, 1);
    final lastDayOfMonth = DateTime(start.year, start.month + 1, 0, 23, 59, 59, 999);
    
    return start.year == firstDayOfMonth.year &&
           start.month == firstDayOfMonth.month &&
           start.day == firstDayOfMonth.day &&
           start.hour == firstDayOfMonth.hour &&
           start.minute == firstDayOfMonth.minute &&
           end.year == lastDayOfMonth.year &&
           end.month == lastDayOfMonth.month &&
           end.day == lastDayOfMonth.day;
  }
  
  void _selectPresetRange(String preset) {
    final now = DateTime.now();
    DateRange? newDateRange;
    
    switch (preset) {
      case 'today':
        final startDate = DateTime(now.year, now.month, now.day);
        newDateRange = DateRange(startDate: startDate, endDate: now);
        break;
      case 'last7days':
        final startDate = now.subtract(const Duration(days: 7));
        newDateRange = DateRange(startDate: startDate, endDate: now);
        break;
      case 'last30days':
        final startDate = now.subtract(const Duration(days: 30));
        newDateRange = DateRange(startDate: startDate, endDate: now);
        break;
      case 'last365days':
        final startDate = now.subtract(const Duration(days: 365));
        newDateRange = DateRange(startDate: startDate, endDate: now);
        break;
      default:
        // Handle month presets like "month-2025-06"
        if (preset.startsWith('month-')) {
          final monthPart = preset.substring(6); // Remove "month-"
          final parts = monthPart.split('-');
          if (parts.length == 2) {
            final year = int.tryParse(parts[0]);
            final month = int.tryParse(parts[1]);
            if (year != null && month != null) {
              final startDate = DateTime(year, month, 1);
              final endDate = DateTime(year, month + 1, 0, 23, 59, 59, 999);
              newDateRange = DateRange(startDate: startDate, endDate: endDate);
            }
          }
        }
        break;
    }
    
    if (newDateRange != null) {
      setState(() {
        _selectedDateRange = newDateRange;
      });
      
      _updateUrlWithDateRange(newDateRange);
    }
  }

  void _selectCustomDateRange() async {
    final picked = await showDateRangePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
      initialDateRange: _selectedDateRange != null
          ? DateTimeRange(
              start: _selectedDateRange!.startDate ?? DateTime.now().subtract(const Duration(days: 30)),
              end: _selectedDateRange!.endDate ?? DateTime.now(),
            )
          : DateTimeRange(
              start: DateTime.now().subtract(const Duration(days: 30)),
              end: DateTime.now(),
            ),
    );
    
    if (picked != null) {
      final newDateRange = DateRange(
        startDate: picked.start,
        endDate: picked.end,
      );
      
      setState(() {
        _selectedDateRange = newDateRange;
      });
      
      _updateUrlWithDateRange(newDateRange);
    }
  }

  String _getDateRangeDisplayText() {
    if (_selectedDateRange == null) return 'Select Date Range';
    
    final start = _selectedDateRange!.startDate;
    final end = _selectedDateRange!.endDate;
    
    if (start == null || end == null) return 'Select Date Range';
    
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    // Check for preset ranges
    if (start.year == today.year && start.month == today.month && start.day == today.day) {
      return 'Today';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 7)))) {
      return 'Last 7 days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 30)))) {
      return 'Last 30 days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 365)))) {
      return 'Last 365 days';
    } else if (_isMonthRange(start, end)) {
      return _getMonthName(start.month, start.year);
    } else {
      return '${_formatDate(start)} - ${_formatDate(end)}';
    }
  }

  String _getMonthName(int month, int year) {
    const monthNames = [
      'January', 'February', 'March', 'April', 'May', 'June',
      'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return '${monthNames[month - 1]} $year';
  }
  
  bool _isApproximately(DateTime date1, DateTime date2) {
    return (date1.difference(date2).inDays.abs() <= 1);
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
              children: [
                Icon(Icons.today),
                SizedBox(width: 8),
                Text('Today'),
              ],
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
        
        // Add last 3 months
        for (int i = 0; i < 3; i++) {
          final month = DateTime(now.year, now.month - i, 1);
          final monthName = _getMonthName(month.month, month.year);
          final value = 'month-${month.year}-${month.month.toString().padLeft(2, '0')}';
          
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
      child: FilledButton.icon(
        onPressed: null,
        icon: const Icon(Icons.date_range),
        label: Text(_getDateRangeDisplayText()),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final testSummaryAsync = ref.watch(testSummaryProvider(_selectedDateRange));

    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: Spacing.level5),
          testSummaryAsync.when(
            data: (data) => _buildPageHeader(data),
            loading: () => Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Success Rate by Test Case',
                  style: Theme.of(context).textTheme.headlineLarge,
                ),
                _buildDateRangeSelector(),
              ],
            ),
            error: (error, stack) => Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Success Rate by Test Case',
                  style: Theme.of(context).textTheme.headlineLarge,
                ),
                _buildDateRangeSelector(),
              ],
            ),
          ),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: SingleChildScrollView(
              child: _buildTestSummarySection(testSummaryAsync),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPageHeader(Map<String, dynamic> data) {
    final totalTests = data['total_tests'] ?? 0;
    final totalExecutions = data['total_executions'] ?? 0;
    final numberFormat = NumberFormat('#,###');
    
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Expanded(
          child: Row(
            children: [
              Text(
                'Success Rate by Test Case',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              const SizedBox(width: Spacing.level4),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Text(
                  '${numberFormat.format(totalTests)} tests • ${numberFormat.format(totalExecutions)} executions',
                  style: Theme.of(context).textTheme.labelLarge?.copyWith(
                    color: Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
            ],
          ),
        ),
        _buildDateRangeSelector(),
      ],
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
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        onChanged: onChanged,
      ),
    );
  }

  Widget _buildTestSummarySection(AsyncValue<Map<String, dynamic>> testSummaryAsync) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const SizedBox(), // Empty space for alignment
            _buildFilterTextField(
              hintText: 'Filter tests...',
              value: _testSummaryFilterText,
              onChanged: (value) {
                setState(() {
                  _testSummaryFilterText = value;
                });
              },
            ),
          ],
        ),
        const SizedBox(height: Spacing.level4),
        testSummaryAsync.when(
          data: (data) => _buildTestSummaryContent(data),
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, stack) => Center(
            child: Text('Error: $error'),
          ),
        ),
      ],
    );
  }

  Widget _buildTestSummaryContent(Map<String, dynamic> data) {
    var summary = data['summary'] as List<dynamic>? ?? [];

    if (summary.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No test results found for the selected period'),
        ),
      );
    }

    // Apply filtering
    if (_testSummaryFilterText.isNotEmpty) {
      final filterLower = _testSummaryFilterText.toLowerCase();
      summary = summary.where((item) {
        return (item['test_identifier']?.toString().toLowerCase().contains(filterLower) ?? false);
      }).toList();
    }

    // Apply sorting
    if (_testSummarySortColumnIndex != null) {
      summary.sort((a, b) {
        dynamic aValue, bValue;
        switch (_testSummarySortColumnIndex) {
          case 0:
            aValue = a['test_identifier'] ?? '';
            bValue = b['test_identifier'] ?? '';
            break;
          case 1:
            aValue = a['total'] ?? 0;
            bValue = b['total'] ?? 0;
            break;
          case 2:
            aValue = a['passed'] ?? 0;
            bValue = b['passed'] ?? 0;
            break;
          case 3:
            aValue = a['failed'] ?? 0;
            bValue = b['failed'] ?? 0;
            break;
          case 4:
            // Calculate fail rate for sorting
            final aTotal = a['total'] ?? 0;
            final aFailed = a['failed'] ?? 0;
            final bTotal = b['total'] ?? 0;
            final bFailed = b['failed'] ?? 0;
            aValue = aTotal > 0 ? (aFailed / aTotal * 100) : 0.0;
            bValue = bTotal > 0 ? (bFailed / bTotal * 100) : 0.0;
            break;
          default:
            return 0;
        }
        
        final comparison = aValue.compareTo(bValue);
        return _testSummarySortAscending ? comparison : -comparison;
      });
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Test Results (Showing ${summary.length} entries)',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        _buildTestTable(summary),
      ],
    );
  }


  Widget _buildTestTable(List<dynamic> summary) {
    // Apply sorting to summary data
    final sortedSummary = List<dynamic>.from(summary);
    if (_testSummarySortColumnIndex != null) {
      sortedSummary.sort((a, b) {
        dynamic aValue, bValue;
        switch (_testSummarySortColumnIndex) {
          case 0:
            aValue = a['test_identifier'] ?? '';
            bValue = b['test_identifier'] ?? '';
            break;
          case 1:
            aValue = a['total'] ?? 0;
            bValue = b['total'] ?? 0;
            break;
          case 2:
            aValue = a['passed'] ?? 0;
            bValue = b['passed'] ?? 0;
            break;
          case 3:
            aValue = a['failed'] ?? 0;
            bValue = b['failed'] ?? 0;
            break;
          case 4:
            // Calculate fail rate for sorting
            final aTotal = a['total'] ?? 0;
            final aFailed = a['failed'] ?? 0;
            final bTotal = b['total'] ?? 0;
            final bFailed = b['failed'] ?? 0;
            aValue = aTotal > 0 ? (aFailed / aTotal * 100) : 0.0;
            bValue = bTotal > 0 ? (bFailed / bTotal * 100) : 0.0;
            break;
          default:
            return 0;
        }
        
        final comparison = aValue.compareTo(bValue);
        return _testSummarySortAscending ? comparison : -comparison;
      });
    }
    
    // Only update test identifiers if the summary data actually changed
    if (_cachedSummaryData == null || !_listEquals(_cachedSummaryData!, summary)) {
      _cachedSummaryData = List.from(summary);
      _cachedTestIdentifiers = summary.map<String>((item) => item['test_identifier'] ?? '').toList();
    }
    
    // Make a single batch request for all test cases using cached identifiers
    final batchIssuesAsync = ref.watch(batchTestCaseIssuesProvider(_cachedTestIdentifiers!));
    
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
              Expanded(
                flex: 3,
                child: _buildSortableHeader('Test', 0),
              ),
              Expanded(
                child: _buildSortableHeader('Total', 1),
              ),
              Expanded(
                child: _buildSortableHeader('Passed', 2),
              ),
              Expanded(
                child: _buildSortableHeader('Failed', 3),
              ),
              Expanded(
                child: _buildSortableHeader('Fail Rate', 4),
              ),
            ],
          ),
        ),
        // Table rows
        Container(
          decoration: BoxDecoration(
            border: Border.all(color: Theme.of(context).dividerColor),
            borderRadius: const BorderRadius.vertical(bottom: Radius.circular(8)),
          ),
          child: batchIssuesAsync.when(
            data: (issuesMap) => Column(
              children: sortedSummary.map<Widget>((item) {
                final testIdentifier = item['test_identifier'] ?? '';
                final isExpanded = _expandedTestCases.contains(testIdentifier);
                final hasIssues = issuesMap[testIdentifier] ?? false;
                return _buildTestRow(item, isExpanded, hasIssues);
              }).toList(),
            ),
            loading: () => Column(
              children: sortedSummary.map<Widget>((item) {
                final testIdentifier = item['test_identifier'] ?? '';
                final isExpanded = _expandedTestCases.contains(testIdentifier);
                return _buildTestRow(item, isExpanded, false); // Default to no issues while loading
              }).toList(),
            ),
            error: (error, stack) => Column(
              children: sortedSummary.map<Widget>((item) {
                final testIdentifier = item['test_identifier'] ?? '';
                final isExpanded = _expandedTestCases.contains(testIdentifier);
                return _buildTestRow(item, isExpanded, false); // Default to no issues on error
              }).toList(),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTestRow(Map<String, dynamic> item, bool isExpanded, bool hasIssues) {
    final numberFormat = NumberFormat('#,###');
    final testIdentifier = item['test_identifier'] ?? '';
    final total = item['total'] ?? 0;
    final failed = item['failed'] ?? 0;
    final failRate = total > 0 ? (failed / total * 100) : 0.0;

    return Column(
      children: [
        _buildRowContent(
          testIdentifier,
          item,
          isExpanded,
          hasIssues,
          numberFormat,
          total,
          failed,
          failRate,
        ),
        if (isExpanded) _buildExpandedContent(testIdentifier),
      ],
    );
  }

  Widget _buildRowContent(
    String testIdentifier,
    Map<String, dynamic> item,
    bool isExpanded,
    bool hasIssues,
    NumberFormat numberFormat,
    int total,
    int failed,
    double failRate,
  ) {
    final rowChild = Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
        color: hasIssues && isExpanded
            ? Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.1)
            : null,
      ),
      child: Row(
        children: [
          SizedBox(
            width: 24,
            child: hasIssues
                ? Icon(
                    isExpanded ? Icons.expand_less : Icons.expand_more,
                    size: 20,
                    color: Theme.of(context).colorScheme.primary,
                  )
                : null,
          ),
          const SizedBox(width: 4),
          Expanded(
            flex: 3,
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    testIdentifier,
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                ),
                if (hasIssues) ...[
                  const SizedBox(width: 4),
                  Icon(
                    Icons.info_outline,
                    size: 16,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                ],
              ],
            ),
          ),
          Expanded(
            child: Text(
              numberFormat.format(total),
              textAlign: TextAlign.right,
            ),
          ),
          Expanded(
            child: Text(
              numberFormat.format(item['passed'] ?? 0),
              textAlign: TextAlign.right,
            ),
          ),
          Expanded(
            child: Text(
              numberFormat.format(failed),
              textAlign: TextAlign.right,
            ),
          ),
          Expanded(
            child: Text(
              '${failRate.toStringAsFixed(1)}%',
              textAlign: TextAlign.right,
            ),
          ),
        ],
      ),
    );

    if (hasIssues) {
      return InkWell(
        onTap: () {
          setState(() {
            if (isExpanded) {
              _expandedTestCases.remove(testIdentifier);
            } else {
              _expandedTestCases.add(testIdentifier);
            }
          });
        },
        child: rowChild,
      );
    } else {
      return rowChild;
    }
  }

  Widget _buildExpandedContent(String testIdentifier) {
    final issuesAsync = ref.watch(testCaseIssuesProvider(testIdentifier));

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
        border: Border(
          bottom: BorderSide(color: Theme.of(context).dividerColor),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Reported Issues',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          issuesAsync.when(
            data: (issues) {
              if (issues.isEmpty) {
                return const Text('No reported issues found for this test case.');
              }
              return Column(
                children: issues.map<Widget>((issue) {
                  return Container(
                    margin: const EdgeInsets.only(bottom: 8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Theme.of(context).dividerColor),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              Icons.bug_report,
                              size: 16,
                              color: Theme.of(context).colorScheme.error,
                            ),
                            const SizedBox(width: 4),
                            Expanded(
                              child: Text(
                                issue['description'] ?? 'No description',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  fontWeight: FontWeight.w500,
                                ),
                              ),
                            ),
                          ],
                        ),
                        if (issue['url'] != null && issue['url'].toString().isNotEmpty) ...[
                          const SizedBox(height: 4),
                          InkWell(
                            onTap: () async {
                              final url = Uri.parse(issue['url']);
                              if (await canLaunchUrl(url)) {
                                await launchUrl(url);
                              }
                            },
                            child: Text(
                              issue['url'],
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Theme.of(context).colorScheme.primary,
                                decoration: TextDecoration.underline,
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  );
                }).toList(),
              );
            },
            loading: () => const Center(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: CircularProgressIndicator(),
              ),
            ),
            error: (error, stack) => Text(
              'Error loading issues: $error',
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSortableHeader(String title, int columnIndex) {
    final isSelected = _testSummarySortColumnIndex == columnIndex;
    
    return InkWell(
      onTap: () {
        setState(() {
          if (_testSummarySortColumnIndex == columnIndex) {
            _testSummarySortAscending = !_testSummarySortAscending;
          } else {
            _testSummarySortColumnIndex = columnIndex;
            _testSummarySortAscending = true;
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
                color: isSelected ? Theme.of(context).colorScheme.primary : null,
              ),
              textAlign: columnIndex == 0 ? TextAlign.left : TextAlign.right,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (isSelected) ...[
            const SizedBox(width: 4),
            Icon(
              _testSummarySortAscending ? Icons.arrow_upward : Icons.arrow_downward,
              size: 16,
              color: Theme.of(context).colorScheme.primary,
            ),
          ],
        ],
      ),
    );
  }

  bool _listEquals(List<dynamic> a, List<dynamic> b) {
    if (a.length != b.length) return false;
    for (int i = 0; i < a.length; i++) {
      if (a[i]['test_identifier'] != b[i]['test_identifier']) return false;
    }
    return true;
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}