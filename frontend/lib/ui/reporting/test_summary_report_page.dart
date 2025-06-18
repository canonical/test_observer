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
import '../common/error_display.dart';

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
  
  // Filter to hide test cases with 0 fails
  bool _hideZeroFails = false;
  
  // Filter to hide closed issues
  bool _hideClosedIssues = true;
  
  // Selected family types for filtering
  Set<String> _selectedFamilies = {'snap', 'deb'};
  
  // Track expanded test cases
  final Set<String> _expandedTestCases = <String>{};
  
  // Track if all issues are expanded
  bool _allIssuesExpanded = false;
  
  // Track expanded environment sections per artefact (test_identifier -> artefact_id -> {'success': bool, 'failure': bool})
  final Map<String, Map<int, Map<String, bool>>> _expandedTestCaseEnvironmentSections = <String, Map<int, Map<String, bool>>>{};
  
  // Cache test identifiers to avoid repeated API calls
  List<String>? _cachedTestIdentifiers;
  Map<String, bool>? _cachedBatchIssues;

  @override
  void initState() {
    super.initState();
    // Set default date range to Last 180 days
    final now = DateTime.now();
    _selectedDateRange = DateRange(
      startDate: now.subtract(const Duration(days: 180)),
      endDate: now,
    );
    
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initializeDateRangeFromUrl();
    });
  }

  void _initializeDateRangeFromUrl() {
    final uri = GoRouterState.of(context).uri;
    final dateRangeParam = uri.queryParameters['date_range'];
    final sortColumnParam = uri.queryParameters['sort_column'];
    final sortOrderParam = uri.queryParameters['sort_order'];
    final hideZeroFailsParam = uri.queryParameters['hide_zero_fails'];
    final hideClosedIssuesParam = uri.queryParameters['hide_closed_issues'];
    final familiesParam = uri.queryParametersAll['families'];
    
    if (dateRangeParam != null) {
      final dateRange = _parseDateRangeFromUrl(dateRangeParam);
      if (dateRange != null) {
        setState(() {
          _selectedDateRange = dateRange;
        });
      }
    } else {
      // If no date range in URL, update URL to reflect the default
      _updateUrlWithDateRange(_selectedDateRange);
    }
    
    // Initialize sort parameters from URL
    if (sortColumnParam != null) {
      final columnIndex = int.tryParse(sortColumnParam);
      if (columnIndex != null && columnIndex >= 0 && columnIndex <= 4) {
        setState(() {
          _testSummarySortColumnIndex = columnIndex;
          _testSummarySortAscending = sortOrderParam == 'asc';
        });
      }
    }
    
    // Initialize filter parameters from URL
    if (hideZeroFailsParam != null) {
      setState(() {
        _hideZeroFails = hideZeroFailsParam.toLowerCase() == 'true';
      });
    }
    
    // Set hideClosedIssues based on URL parameter, defaulting to true
    setState(() {
      _hideClosedIssues = hideClosedIssuesParam != null 
          ? hideClosedIssuesParam.toLowerCase() == 'true'
          : true; // Default to true (hide closed issues)
    });
    
    // Initialize families from URL parameter
    if (familiesParam != null && familiesParam.isNotEmpty) {
      setState(() {
        _selectedFamilies = familiesParam.toSet();
      });
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
      } else if (dateRangeParam == 'last180days') {
        final now = DateTime.now();
        return DateRange(startDate: now.subtract(const Duration(days: 180)), endDate: now);
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

  void _updateUrlWithSort() {
    final currentUri = GoRouterState.of(context).uri;
    final queryParams = Map<String, String>.from(currentUri.queryParameters);
    
    if (_testSummarySortColumnIndex != null) {
      queryParams['sort_column'] = _testSummarySortColumnIndex.toString();
      queryParams['sort_order'] = _testSummarySortAscending ? 'asc' : 'desc';
    } else {
      queryParams.remove('sort_column');
      queryParams.remove('sort_order');
    }
    
    final newUri = currentUri.replace(queryParameters: queryParams.isEmpty ? null : queryParams);
    context.go(newUri.toString());
  }

  void _updateUrlWithFilter() {
    final currentUri = GoRouterState.of(context).uri;
    final queryParams = Map<String, dynamic>.from(currentUri.queryParameters);
    
    if (_hideZeroFails) {
      queryParams['hide_zero_fails'] = 'true';
    } else {
      queryParams.remove('hide_zero_fails');
    }
    
    if (_hideClosedIssues) {
      queryParams['hide_closed_issues'] = 'true';
    } else {
      queryParams.remove('hide_closed_issues');
    }
    
    // Remove old families params and add new ones
    queryParams.removeWhere((key, value) => key == 'families');
    
    // Convert to List<List<String>> for proper URL encoding
    final queryList = <String>[];
    queryParams.forEach((key, value) {
      if (value != null) {
        queryList.add('$key=$value');
      }
    });
    
    // Add families as separate parameters
    for (final family in _selectedFamilies) {
      queryList.add('families=$family');
    }
    
    final newQuery = queryList.isEmpty ? null : queryList.join('&');
    final newUri = currentUri.replace(query: newQuery);
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
    } else if (_isApproximately(start, now.subtract(const Duration(days: 180)))) {
      return 'last180days';
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
      case 'last180days':
        final startDate = now.subtract(const Duration(days: 180));
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
    } else if (_isApproximately(start, now.subtract(const Duration(days: 180)))) {
      return 'Last 180 days';
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
              _getDateRangeDisplayText(),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(width: 4),
            const Icon(Icons.arrow_drop_down, size: 16),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final testSummaryParams = TestSummaryParams(
      dateRange: _selectedDateRange,
      families: _selectedFamilies.toList(),
    );
    final testSummaryAsync = ref.watch(testSummaryProvider(testSummaryParams));

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
            loading: () => _buildLoadingHeader(),
            error: (error, stack) => Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Test Case Health',
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

  Widget _buildLoadingHeader() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Row(
                children: [
                  Text(
                    'Test Case Health',
                    style: Theme.of(context).textTheme.headlineLarge,
                  ),
                  const SizedBox(width: Spacing.level4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        SizedBox(
                          width: 16,
                          height: 16,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Loading test data...',
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Row(
              children: [
                _buildDateRangeSelector(),
                const SizedBox(width: Spacing.level3),
                _buildFamilyDropdown(),
                const SizedBox(width: Spacing.level3),
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
          ],
        ),
      ],
    );
  }

  Widget _buildLoadingContent() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(
          Spacing.level5, 
          Spacing.level5 * 3, // More vertical spacing from top
          Spacing.level5, 
          Spacing.level5
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            SizedBox(
              width: 80,
              height: 80,
              child: CircularProgressIndicator(
                strokeWidth: 6,
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(height: Spacing.level5),
            Text(
              'Loading Test Health Data',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: Theme.of(context).colorScheme.primary,
              ),
            ),
            const SizedBox(height: Spacing.level3),
            Text(
              'Analyzing test results and calculating statistics...',
              style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPageHeader(Map<String, dynamic> data) {
    final totalTests = data['total_tests'] ?? 0;
    final totalExecutions = data['total_executions'] ?? 0;
    final summary = data['summary'] as List<dynamic>? ?? [];
    final numberFormat = NumberFormat('#,###');
    
    // Calculate overall failure rate
    int totalPassed = 0;
    int totalAll = 0;
    for (final item in summary) {
      totalPassed += (item['passed'] ?? 0) as int;
      totalAll += (item['total'] ?? 0) as int;
    }
    final failureRate = totalAll > 0 ? ((totalAll - totalPassed) / totalAll * 100) : 0.0;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Row(
                children: [
                  Text(
                    'Test Case Fail Rate',
                    style: Theme.of(context).textTheme.headlineLarge,
                  ),
                  const SizedBox(width: Spacing.level4),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${numberFormat.format(totalTests)} tests • ${numberFormat.format(totalExecutions)} executions',
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ),
                        Text(
                          'Total fail rate: ${failureRate.toStringAsFixed(1)}%',
                          style: Theme.of(context).textTheme.labelLarge?.copyWith(
                            color: Theme.of(context).colorScheme.onPrimaryContainer.withValues(alpha: 0.8),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Row(
              children: [
                _buildDateRangeSelector(),
                const SizedBox(width: Spacing.level3),
                _buildFamilyDropdown(),
                const SizedBox(width: Spacing.level3),
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
          ],
        ),
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
        const SizedBox(height: Spacing.level4),
        testSummaryAsync.when(
          data: (data) => _buildTestSummaryContent(data),
          loading: () => _buildLoadingContent(),
          error: (error, stack) => Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.error_outline, size: 48, color: Colors.red),
                const SizedBox(height: 16),
                const Text('Failed to load test summary data'),
                const SizedBox(height: 8),
                ElevatedButton.icon(
                  onPressed: () => showErrorDialog(
                    context,
                    error,
                    title: 'Test Summary Error',
                    onRetry: () => ref.invalidate(testSummaryProvider),
                  ),
                  icon: const Icon(Icons.info),
                  label: const Text('View Details'),
                ),
              ],
            ),
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
    
    // Apply zero-fails filter
    if (_hideZeroFails) {
      summary = summary.where((item) {
        final failed = (item['total'] ?? 0) - (item['passed'] ?? 0);
        return failed > 0;
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
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                Text(
                  'Test Results (Showing ${summary.length} entries)',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                // Add expand/collapse all control only if there are test cases with issues
                if (_hasTestCasesWithIssues(summary)) ...[
                  const SizedBox(width: 12),
                  TextButton.icon(
                    onPressed: () {
                      setState(() {
                        _allIssuesExpanded = !_allIssuesExpanded;
                        if (_allIssuesExpanded) {
                          // Expand all test cases that have issues
                          for (final item in summary) {
                            final testIdentifier = item['test_identifier'] ?? '';
                            final batchIssues = _cachedBatchIssues ?? <String, bool>{};
                            final hasIssues = batchIssues[testIdentifier] ?? false;
                            if (hasIssues) {
                              _expandedTestCases.add(testIdentifier);
                            }
                          }
                        } else {
                          // Collapse all test cases
                          _expandedTestCases.clear();
                        }
                      });
                    },
                    icon: Icon(
                      _allIssuesExpanded ? Icons.expand_less : Icons.expand_more,
                      size: 18,
                    ),
                    label: Text(
                      _allIssuesExpanded ? 'Collapse All' : 'Expand All',
                      style: Theme.of(context).textTheme.labelSmall,
                    ),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Checkbox(
                      value: _hideZeroFails,
                      onChanged: (value) {
                        setState(() {
                          _hideZeroFails = value ?? false;
                        });
                        _updateUrlWithFilter();
                      },
                    ),
                    const Text('Hide always successful tests'),
                  ],
                ),
                const SizedBox(width: 24),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Checkbox(
                      value: _hideClosedIssues,
                      onChanged: (value) {
                        setState(() {
                          _hideClosedIssues = value ?? false;
                        });
                        _updateUrlWithFilter();
                      },
                    ),
                    const Text('Hide closed reported issues'),
                  ],
                ),
              ],
            ),
          ],
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
    
    // Only update test identifiers if the actual set of test identifiers changed
    final currentTestIdentifiers = summary.map<String>((item) => item['test_identifier'] ?? '').toSet();
    final cachedTestIdentifiersSet = _cachedTestIdentifiers?.toSet() ?? <String>{};
    
    if (!_setEquals(currentTestIdentifiers, cachedTestIdentifiersSet)) {
      _cachedTestIdentifiers = currentTestIdentifiers.toList();
      _cachedBatchIssues = null; // Clear cache when identifiers change
      // Trigger the batch request only when test identifiers actually change
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _loadBatchIssues(ref);
      });
    }
    
    // If we have identifiers but no cached issues yet, trigger initial load
    if (_cachedTestIdentifiers != null && _cachedTestIdentifiers!.isNotEmpty && _cachedBatchIssues == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _loadBatchIssues(ref);
      });
    }
    
    // Use cached batch issues if available, otherwise show loading
    final batchIssuesAsync = _cachedBatchIssues != null 
        ? AsyncValue.data(_cachedBatchIssues!) 
        : const AsyncValue.loading();
    
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
              SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.centerRight,
                  child: _buildSortableHeader('Total', 1),
                ),
              ),
              SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.centerRight,
                  child: _buildSortableHeader('Passed', 2),
                ),
              ),
              SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.centerRight,
                  child: _buildSortableHeader('Failed', 3),
                ),
              ),
              SizedBox(
                width: 80,
                child: Align(
                  alignment: Alignment.centerRight,
                  child: _buildSortableHeader('Fail Rate', 4),
                ),
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
              ],
            ),
          ),
          SizedBox(
            width: 80,
            child: Text(
              numberFormat.format(total),
              textAlign: TextAlign.right,
            ),
          ),
          SizedBox(
            width: 80,
            child: Text(
              numberFormat.format(item['passed'] ?? 0),
              textAlign: TextAlign.right,
            ),
          ),
          SizedBox(
            width: 80,
            child: Text(
              numberFormat.format(failed),
              textAlign: TextAlign.right,
            ),
          ),
          SizedBox(
            width: 80,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                Text(
                  '${failRate.toStringAsFixed(1)}%',
                  textAlign: TextAlign.right,
                ),
                // Add trend arrow with tooltip
                if (item['trend'] != null && item['trend'] != 'none') ...[
                  const SizedBox(width: 4),
                  Tooltip(
                    message: item['previous_success_rate'] != null
                        ? '${(100 - item['previous_success_rate']).toStringAsFixed(1)}% fail rate on previous ${_getPeriodDescription()}'
                        : 'No data for previous period',
                    child: Icon(
                      item['trend'] == 'improving' ? Icons.south_east : Icons.north_east,
                      size: 16,
                      color: item['trend'] == 'improving' ? Colors.green : Colors.red,
                    ),
                  ),
                ],
              ],
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
              // Apply closed issues filter
              var filteredIssues = issues;
              if (_hideClosedIssues) {
                filteredIssues = issues.where((issue) => issue['issue_status'] != 'CLOSED').toList();
              }
              
              if (filteredIssues.isEmpty) {
                return const Text('No reported, open issues found for this test case.');
              }
              return Column(
                children: filteredIssues.map<Widget>((issue) {
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
                            _buildStatusChip(issue['issue_status']),
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
            error: (error, stack) => Row(
              children: [
                Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Failed to load issue information',
                    style: TextStyle(color: Theme.of(context).colorScheme.error),
                  ),
                ),
                TextButton(
                  onPressed: () => showErrorSnackbar(context, error),
                  child: const Text('Details'),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
          Text(
            'Associated Artefacts',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          _buildTestCaseAffectedArtefacts(testIdentifier),
        ],
      ),
    );
  }

  Widget _buildTestCaseAffectedArtefacts(String testIdentifier) {
    final artefactsAsync = ref.watch(testCaseAffectedArtefactsProvider(testIdentifier));

    return artefactsAsync.when(
      data: (data) {
        final successOnlyArtefacts = data['success_only_artefacts'] as List? ?? [];
        final artefactsWithFailures = data['artefacts_with_failures'] as List? ?? [];
        final totalArtefacts = data['total_artefacts'] as int? ?? 0;

        if (totalArtefacts == 0) {
          return const Text('No associated artefacts found for this test case.');
        }

        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (artefactsWithFailures.isNotEmpty) ...[
              _buildArtefactSection(
                '... artefacts where some environments failed this test',
                artefactsWithFailures,
                testIdentifier,
                Theme.of(context).colorScheme.surfaceContainerHighest,
                Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(height: 12),
            ],
            if (successOnlyArtefacts.isNotEmpty) ...[
              _buildArtefactSection(
                'Success-Only Artefacts',
                successOnlyArtefacts,
                testIdentifier,
                Colors.green.shade100,
                Colors.green.shade700,
              ),
            ],
          ],
        );
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
            Icon(Icons.error_outline, color: Theme.of(context).colorScheme.error),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Failed to load associated artefacts',
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
            TextButton(
              onPressed: () => showErrorSnackbar(context, error),
              child: const Text('Details'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildArtefactSection(String title, List artefacts, String testIdentifier, Color backgroundColor, Color borderColor) {
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
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: borderColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(color: borderColor.withValues(alpha: 0.2)),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.inventory_2,
                        size: 16,
                        color: borderColor,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          groupName,
                          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: borderColor,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
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
                      Icon(
                        Icons.open_in_new,
                        size: 12,
                        color: borderColor,
                      ),
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
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                            decoration: BoxDecoration(
                              color: Theme.of(context).colorScheme.secondaryContainer,
                              borderRadius: BorderRadius.circular(4),
                            ),
                            child: Text(
                              artefact['family'].toString().toUpperCase(),
                              style: TextStyle(
                                color: Theme.of(context).colorScheme.onSecondaryContainer,
                                fontSize: 9,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                          if (artefact['due_date'] != null && artefact['due_date'] != 'null') ...[
                            const SizedBox(width: 6),
                            Icon(
                              Icons.schedule,
                              size: 12,
                              color: Theme.of(context).colorScheme.onSurfaceVariant,
                            ),
                            const SizedBox(width: 2),
                            Text(
                              _formatDate(DateTime.parse(artefact['due_date'])),
                              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: Theme.of(context).colorScheme.onSurfaceVariant,
                                fontSize: 10,
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      _buildTestCaseEnvironmentSection(artefact, testIdentifier),
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

  Widget _buildTestCaseEnvironmentSection(Map<String, dynamic> artefact, String testIdentifier) {
    final environmentDetails = artefact['environment_details'] as List? ?? [];
    final failureEnvironments = artefact['failure_environments'] as List? ?? [];
    final totalEnvCount = artefact['environment_count'] as int? ?? 0;
    final artefactId = artefact['id'] as int;
    
    if (totalEnvCount == 0) {
      return Text(
        'Environments: 0 environments',
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
        ),
      );
    }

    final isEnvExpanded = _expandedTestCaseEnvironmentSections[testIdentifier]?[artefactId]?['environments'] ?? (environmentDetails.length < 10);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: environmentDetails.isNotEmpty ? () {
            setState(() {
              _expandedTestCaseEnvironmentSections.putIfAbsent(testIdentifier, () => <int, Map<String, bool>>{});
              _expandedTestCaseEnvironmentSections[testIdentifier]!.putIfAbsent(artefactId, () => <String, bool>{});
              _expandedTestCaseEnvironmentSections[testIdentifier]![artefactId]!['environments'] = !isEnvExpanded;
            });
          } : null,
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
                  decoration: environmentDetails.isNotEmpty ? TextDecoration.underline : null,
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
              color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Wrap(
              spacing: 4,
              runSpacing: 4,
              children: environmentDetails.map<Widget>((envDetail) {
                final envName = envDetail['name'] as String;
                final c3Link = envDetail['c3_link'] as String?;
                final hasFailure = envDetail['has_failure'] as bool? ?? false;
                
                return InkWell(
                  onTap: c3Link != null && c3Link.isNotEmpty 
                    ? () => _launchUrl(c3Link)
                    : () => _launchTestflingerUrl(envName),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: hasFailure 
                        ? Colors.red.shade100
                        : Theme.of(context).colorScheme.primaryContainer,
                      borderRadius: BorderRadius.circular(4),
                      border: Border.all(
                        color: hasFailure 
                          ? Colors.red.shade300
                          : Theme.of(context).colorScheme.outline.withValues(alpha: 0.3),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          envName,
                          style: TextStyle(
                            color: hasFailure 
                              ? Colors.red.shade800
                              : Theme.of(context).colorScheme.onPrimaryContainer,
                            fontSize: 11,
                            fontWeight: hasFailure ? FontWeight.bold : FontWeight.normal,
                            decoration: TextDecoration.underline,
                          ),
                        ),
                        if (c3Link != null && c3Link.isNotEmpty) ...[
                          const SizedBox(width: 4),
                          Icon(
                            Icons.launch,
                            size: 10,
                            color: hasFailure 
                              ? Colors.red.shade600
                              : Theme.of(context).colorScheme.onPrimaryContainer,
                          ),
                        ],
                      ],
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

  Widget _buildTestCaseEnvironmentSubSection(
    String title,
    List environments,
    String testIdentifier,
    int artefactId,
    String sectionType,
    Color backgroundColor,
    Color textColor,
  ) {
    final isExpanded = _expandedTestCaseEnvironmentSections[testIdentifier]?[artefactId]?[sectionType] ?? false;
    
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        InkWell(
          onTap: () {
            setState(() {
              _expandedTestCaseEnvironmentSections.putIfAbsent(testIdentifier, () => <int, Map<String, bool>>{});
              _expandedTestCaseEnvironmentSections[testIdentifier]!.putIfAbsent(artefactId, () => <String, bool>{});
              _expandedTestCaseEnvironmentSections[testIdentifier]![artefactId]![sectionType] = !isExpanded;
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
                    fontWeight: FontWeight.bold,
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
                    padding: const EdgeInsets.symmetric(horizontal: 3, vertical: 1),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surface,
                      borderRadius: BorderRadius.circular(2),
                      border: Border.all(color: textColor.withValues(alpha: 0.2)),
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

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }

  Future<void> _launchTestflingerUrl(String environmentName) async {
    final url = 'https://testflinger.canonical.com/queues/$environmentName';
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }

  Future<void> _launchUrl(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
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
            _testSummarySortAscending = false; // Start with descending order
          }
        });
        _updateUrlWithSort();
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
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        statusValue,
        style: TextStyle(
          color: textColor,
          fontSize: 10,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  bool _setEquals(Set<String> a, Set<String> b) {
    if (a.length != b.length) return false;
    return a.every((item) => b.contains(item));
  }

  bool _hasTestCasesWithIssues(List<dynamic> summary) {
    if (_cachedBatchIssues == null) return false;
    
    for (final item in summary) {
      final testIdentifier = item['test_identifier'] ?? '';
      final hasIssues = _cachedBatchIssues![testIdentifier] ?? false;
      if (hasIssues) return true;
    }
    return false;
  }

  Widget _buildFamilyDropdown() {
    const families = ['snap', 'deb', 'charm', 'image'];
    final selectedText = _selectedFamilies.isEmpty 
        ? "None" 
        : (_selectedFamilies.toList()..sort()).join(", ");
    
    return PopupMenuButton<String>(
      tooltip: 'Select artifact families to include',
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: Theme.of(context).colorScheme.outline),
          borderRadius: BorderRadius.circular(4),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Families: $selectedText',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(width: 8),
            const Icon(Icons.arrow_drop_down, size: 20),
          ],
        ),
      ),
      onSelected: (value) {
        // Handle selection here to avoid context issues
        if (value != null) {
          _toggleFamily(value);
        }
      },
      itemBuilder: (context) {
        return families.map((family) {
          final isSelected = _selectedFamilies.contains(family);
          return PopupMenuItem<String>(
            value: family,
            child: Row(
              children: [
                Checkbox(
                  value: isSelected,
                  onChanged: null, // Disable to avoid double handling
                ),
                Text(family),
              ],
            ),
          );
        }).toList();
      },
    );
  }

  void _toggleFamily(String family) {
    if (mounted) {
      setState(() {
        if (_selectedFamilies.contains(family)) {
          _selectedFamilies.remove(family);
        } else {
          _selectedFamilies.add(family);
        }
      });
      _updateUrlWithFilter();
    }
  }

  void _loadBatchIssues(WidgetRef ref) async {
    if (_cachedTestIdentifiers == null || _cachedTestIdentifiers!.isEmpty) return;
    
    try {
      final result = await ref.read(batchTestCaseIssuesProvider(_cachedTestIdentifiers!).future);
      if (mounted) {
        setState(() {
          _cachedBatchIssues = result;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _cachedBatchIssues = <String, bool>{}; // Empty map on error
        });
      }
    }
  }

  String _getPeriodDescription() {
    if (_selectedDateRange == null) return 'period';
    
    final start = _selectedDateRange!.startDate;
    final end = _selectedDateRange!.endDate;
    
    if (start == null || end == null) return 'period';
    
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    
    // Check for preset ranges
    if (start.year == today.year && start.month == today.month && start.day == today.day) {
      return 'day';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 7)))) {
      return '7 days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 30)))) {
      return '30 days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 180)))) {
      return '180 days';
    } else if (_isApproximately(start, now.subtract(const Duration(days: 365)))) {
      return '365 days';
    } else if (_isMonthRange(start, end)) {
      return 'month';
    } else {
      // Custom range - calculate duration
      final duration = end.difference(start);
      return '${duration.inDays} days';
    }
  }
}