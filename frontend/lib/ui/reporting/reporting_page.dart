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

import '../../providers/reports.dart';
import '../spacing.dart';

class ReportingPage extends ConsumerStatefulWidget {
  const ReportingPage({super.key});

  @override
  ConsumerState<ReportingPage> createState() => _ReportingPageState();
}

class _ReportingPageState extends ConsumerState<ReportingPage> {
  DateRange? _selectedDateRange;
  
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
    final knownIssuesReportAsync = ref.watch(knownIssuesReportProvider);
    final environmentIssuesReportAsync = ref.watch(environmentIssuesReportProvider);

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
                'Reports',
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
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildTestSummarySection(testSummaryAsync),
                  const SizedBox(height: Spacing.level5),
                  _buildKnownIssuesSection(knownIssuesReportAsync),
                  const SizedBox(height: Spacing.level5),
                  _buildEnvironmentIssuesSection(environmentIssuesReportAsync),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildKnownIssuesSection(AsyncValue<Map<String, dynamic>> knownIssuesReportAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Known Test Case Issues',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: Spacing.level4),
            knownIssuesReportAsync.when(
              data: (data) => _buildKnownIssuesContent(data),
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

  Widget _buildEnvironmentIssuesSection(AsyncValue<Map<String, dynamic>> environmentIssuesReportAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Known Environment Issues',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: Spacing.level4),
            environmentIssuesReportAsync.when(
              data: (data) => _buildEnvironmentIssuesContent(data),
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

  Widget _buildTestSummarySection(AsyncValue<Map<String, dynamic>> testSummaryAsync) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Success Rate by Test Case',
              style: Theme.of(context).textTheme.headlineSmall,
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

  Widget _buildKnownIssuesContent(Map<String, dynamic> data) {
    final issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No known issues found'),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Total Issues: $totalCount',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columnSpacing: 12.0,
            horizontalMargin: 8.0,
            columns: const [
              DataColumn(label: Text('ID', style: TextStyle(fontWeight: FontWeight.bold)), numeric: true),
              DataColumn(label: Text('Template ID', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Case Name', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Description', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('URL', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Created At', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Updated At', style: TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: issues.map((issue) {
              final createdAt = DateTime.parse(issue['created_at']);
              final updatedAt = DateTime.parse(issue['updated_at']);

              return DataRow(cells: [
                DataCell(Text(issue['id']?.toString() ?? '')),
                DataCell(
                  SizedBox(
                    width: 200,
                    child: Text(
                      issue['template_id'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 200,
                    child: Text(
                      issue['case_name'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 300,
                    child: Text(
                      issue['description'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      maxLines: 3,
                    ),
                  ),
                ),
                DataCell(
                  InkWell(
                    onTap: () => _launchUrl(issue['url'] ?? ''),
                    child: Text(
                      issue['url'] ?? '',
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.primary,
                        decoration: TextDecoration.underline,
                      ),
                    ),
                  ),
                ),
                DataCell(Text(_formatDateTime(createdAt))),
                DataCell(Text(_formatDateTime(updatedAt))),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildEnvironmentIssuesContent(Map<String, dynamic> data) {
    final issues = data['issues'] as List<dynamic>? ?? [];
    final totalCount = data['total_count'] ?? 0;

    if (issues.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(Spacing.level5),
          child: Text('No known environment issues found'),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Total Issues: $totalCount',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columnSpacing: 12.0,
            horizontalMargin: 8.0,
            columns: const [
              DataColumn(label: Text('ID', style: TextStyle(fontWeight: FontWeight.bold)), numeric: true),
              DataColumn(label: Text('Environment', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Description', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('URL', style: TextStyle(fontWeight: FontWeight.bold))),
              DataColumn(label: Text('Confirmed', style: TextStyle(fontWeight: FontWeight.bold))),
            ],
            rows: issues.map((issue) {
              return DataRow(cells: [
                DataCell(Text(issue.id.toString())),
                DataCell(
                  SizedBox(
                    width: 150,
                    child: Text(
                      issue.environmentName,
                      overflow: TextOverflow.ellipsis,
                      maxLines: 2,
                    ),
                  ),
                ),
                DataCell(
                  SizedBox(
                    width: 300,
                    child: Text(
                      issue.description,
                      overflow: TextOverflow.ellipsis,
                      maxLines: 3,
                    ),
                  ),
                ),
                DataCell(
                  issue.url != null && issue.url.toString().isNotEmpty
                      ? InkWell(
                          onTap: () => _launchUrl(issue.url.toString()),
                          child: Text(
                            issue.url.toString(),
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                              color: Theme.of(context).colorScheme.primary,
                              decoration: TextDecoration.underline,
                            ),
                          ),
                        )
                      : const Text(''),
                ),
                DataCell(
                  Icon(
                    issue.isConfirmed ? Icons.check_circle : Icons.help_outline,
                    color: issue.isConfirmed ? Colors.green : Colors.orange,
                    size: 20,
                  ),
                ),
              ]);
            }).toList(),
          ),
        ),
      ],
    );
  }

  Widget _buildTestSummaryContent(Map<String, dynamic> data) {
    final summary = data['summary'] as List<dynamic>? ?? [];
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
          'Top Test Results',
          style: Theme.of(context).textTheme.titleMedium,
        ),
        const SizedBox(height: Spacing.level3),
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            columns: const [
              DataColumn(label: Text('Test')),
              DataColumn(label: Text('Total'), numeric: true),
              DataColumn(label: Text('Passed'), numeric: true),
              DataColumn(label: Text('Failed'), numeric: true),
              DataColumn(label: Text('Skipped'), numeric: true),
            ],
            rows: summary.take(10).map((item) {
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

  String _formatDateTime(DateTime? dateTime) {
    if (dateTime == null) return 'N/A';
    return '${dateTime.year}-${dateTime.month.toString().padLeft(2, '0')}-${dateTime.day.toString().padLeft(2, '0')} ${dateTime.hour.toString().padLeft(2, '0')}:${dateTime.minute.toString().padLeft(2, '0')}:${dateTime.second.toString().padLeft(2, '0')}';
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}