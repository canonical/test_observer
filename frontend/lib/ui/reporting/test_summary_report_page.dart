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

import '../../providers/reports.dart';
import '../spacing.dart';

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
  
  void _selectDateRange() async {
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
      setState(() {
        _selectedDateRange = DateRange(
          startDate: picked.start,
          endDate: picked.end,
        );
      });
    }
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
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'Test Summary Report',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              FilledButton.icon(
                onPressed: _selectDateRange,
                icon: const Icon(Icons.date_range),
                label: Text(_selectedDateRange != null
                    ? '${_formatDate(_selectedDateRange!.startDate)} - ${_formatDate(_selectedDateRange!.endDate)}'
                    : 'Select Date Range'),
              ),
            ],
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
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Success Rate by Test Case',
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
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
        ),
      ),
    );
  }

  Widget _buildTestSummaryContent(Map<String, dynamic> data) {
    var summary = data['summary'] as List<dynamic>? ?? [];
    final totalTests = data['total_tests'] ?? 0;
    final totalExecutions = data['total_executions'] ?? 0;

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
            aValue = a['skipped'] ?? 0;
            bValue = b['skipped'] ?? 0;
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
          children: [
            _buildStatCard('Total Tests', totalTests.toString(), Icons.list_alt),
            const SizedBox(width: Spacing.level4),
            _buildStatCard('Total Executions', totalExecutions.toString(), Icons.play_circle_outline),
          ],
        ),
        const SizedBox(height: Spacing.level4),
        Text(
          'Test Results (Showing ${summary.length} entries)',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            sortColumnIndex: _testSummarySortColumnIndex,
            sortAscending: _testSummarySortAscending,
            columns: [
              DataColumn(
                label: const Text('Test'),
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _testSummarySortColumnIndex = columnIndex;
                    _testSummarySortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Total'),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _testSummarySortColumnIndex = columnIndex;
                    _testSummarySortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Passed'),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _testSummarySortColumnIndex = columnIndex;
                    _testSummarySortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Failed'),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _testSummarySortColumnIndex = columnIndex;
                    _testSummarySortAscending = ascending;
                  });
                },
              ),
              DataColumn(
                label: const Text('Skipped'),
                numeric: true,
                onSort: (columnIndex, ascending) {
                  setState(() {
                    _testSummarySortColumnIndex = columnIndex;
                    _testSummarySortAscending = ascending;
                  });
                },
              ),
            ],
            rows: summary.map((item) {
              return DataRow(cells: [
                DataCell(Text(
                  item['test_identifier'] ?? '',
                  overflow: TextOverflow.ellipsis,
                  maxLines: 1,
                )),
                DataCell(Text(item['total']?.toString() ?? '0')),
                DataCell(Text(item['passed']?.toString() ?? '0')),
                DataCell(Text(item['failed']?.toString() ?? '0')),
                DataCell(Text(item['skipped']?.toString() ?? '0')),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(Spacing.level4),
          child: Row(
            children: [
              Icon(icon, size: 48, color: Theme.of(context).colorScheme.primary),
              const SizedBox(width: Spacing.level3),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: Theme.of(context).textTheme.titleSmall),
                  Text(value, style: Theme.of(context).textTheme.headlineMedium),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime? date) {
    if (date == null) return 'N/A';
    return '${date.year}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
  }
}