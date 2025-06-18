// Copyright (C) 2025 Canonical Ltd.
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
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';

import '../../providers/reports.dart';
import '../spacing.dart';

class RejectionsReportPage extends ConsumerStatefulWidget {
  const RejectionsReportPage({super.key});

  @override
  ConsumerState<RejectionsReportPage> createState() =>
      _RejectionsReportPageState();
}

class _RejectionsReportPageState extends ConsumerState<RejectionsReportPage> {
  DateRange? _selectedDateRange;
  Set<String> _selectedFamilies = {'snap', 'deb', 'charm', 'image'};

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
    final rejectionsParams = RejectionsParams(
      dateRange: _selectedDateRange,
      families: _selectedFamilies.toList(),
    );

    final rejectionsReportAsync = ref.watch(
      rejectionsReportProvider(rejectionsParams),
    );
    final rejectionsSummaryAsync = ref.watch(
      rejectionsSummaryProvider(rejectionsParams),
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
                'Rejections',
                style: Theme.of(context).textTheme.headlineLarge,
              ),
              Row(
                children: [
                  _buildDateRangeSelector(),
                  const SizedBox(width: Spacing.level3),
                  _buildFamilySelector(),
                ],
              ),
            ],
          ),
          const SizedBox(height: Spacing.level5),

          Expanded(
            child: rejectionsReportAsync.when(
              loading: () => const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: Spacing.level3),
                    Text('Loading rejections data...'),
                  ],
                ),
              ),
              error: (error, stackTrace) => Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(Icons.error, color: Colors.red, size: 48),
                    const SizedBox(height: 16),
                    Text('Error loading rejections data: $error'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => ref.invalidate(rejectionsReportProvider),
                      child: const Text('Retry'),
                    ),
                  ],
                ),
              ),
              data: (rejectionsData) => rejectionsSummaryAsync.when(
                loading: () => const Center(child: CircularProgressIndicator()),
                error: (error, stackTrace) => Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error, color: Colors.red, size: 48),
                      const SizedBox(height: 16),
                      Text('Error loading summary data: $error'),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: () =>
                            ref.invalidate(rejectionsSummaryProvider),
                        child: const Text('Retry'),
                      ),
                    ],
                  ),
                ),
                data: (summaryData) =>
                    _buildReportContent(rejectionsData, summaryData),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDateRangeSelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.5),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.calendar_today, size: 16),
          const SizedBox(width: 8),
          Text(
            _selectedDateRange != null
                ? '${DateFormat.yMMMd().format(_selectedDateRange!.startDate!)} - ${DateFormat.yMMMd().format(_selectedDateRange!.endDate!)}'
                : 'Select date range',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(width: 8),
          PopupMenuButton<String>(
            icon: const Icon(Icons.arrow_drop_down, size: 16),
            onSelected: (value) {
              final now = DateTime.now();
              DateRange? newRange;

              switch (value) {
                case 'last7days':
                  newRange = DateRange(
                    startDate: now.subtract(const Duration(days: 7)),
                    endDate: now,
                  );
                  break;
                case 'last30days':
                  newRange = DateRange(
                    startDate: now.subtract(const Duration(days: 30)),
                    endDate: now,
                  );
                  break;
                case 'last90days':
                  newRange = DateRange(
                    startDate: now.subtract(const Duration(days: 90)),
                    endDate: now,
                  );
                  break;
                case 'last365days':
                  newRange = DateRange(
                    startDate: now.subtract(const Duration(days: 365)),
                    endDate: now,
                  );
                  break;
              }

              if (newRange != null) {
                setState(() {
                  _selectedDateRange = newRange;
                });
              }
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'last7days',
                child: Text('Last 7 days'),
              ),
              const PopupMenuItem(
                value: 'last30days',
                child: Text('Last 30 days'),
              ),
              const PopupMenuItem(
                value: 'last90days',
                child: Text('Last 90 days'),
              ),
              const PopupMenuItem(
                value: 'last365days',
                child: Text('Last 365 days'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFamilySelector() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        border: Border.all(
          color: Theme.of(context).colorScheme.outline.withValues(alpha: 0.5),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.category, size: 16),
          const SizedBox(width: 8),
          Text(
            'Families (${_selectedFamilies.length})',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(width: 8),
          PopupMenuButton<String>(
            icon: const Icon(Icons.arrow_drop_down, size: 16),
            onSelected: (value) {
              setState(() {
                if (_selectedFamilies.contains(value)) {
                  _selectedFamilies.remove(value);
                } else {
                  _selectedFamilies.add(value);
                }
                // Ensure at least one family is selected
                if (_selectedFamilies.isEmpty) {
                  _selectedFamilies.add(value);
                }
              });
            },
            itemBuilder: (context) => ['snap', 'deb', 'charm', 'image']
                .map(
                  (family) => PopupMenuItem(
                    value: family,
                    child: Row(
                      children: [
                        Checkbox(
                          value: _selectedFamilies.contains(family),
                          onChanged: null, // Handled by onSelected above
                        ),
                        Text(family),
                      ],
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _buildReportContent(
    Map<String, dynamic> rejectionsData,
    Map<String, dynamic> summaryData,
  ) {
    final totalRejections = rejectionsData['total_rejections'] as int;
    final timeSeries = rejectionsData['time_series'] as List<dynamic>;
    final rejectionDetails =
        rejectionsData['rejection_details'] as List<dynamic>;
    final familyTotals =
        rejectionsData['family_totals'] as Map<String, dynamic>;

    final topRejectedArtefacts =
        summaryData['top_rejected_artefacts'] as List<dynamic>;
    final topRejectingEnvironments =
        summaryData['top_rejecting_environments'] as List<dynamic>;

    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Summary Cards
          Row(
            children: [
              Expanded(
                child: _buildSummaryCard(
                  'Total Rejections',
                  totalRejections.toString(),
                  Icons.cancel_outlined,
                  Colors.red,
                ),
              ),
              const SizedBox(width: Spacing.level3),
              Expanded(
                child: _buildSummaryCard(
                  'Families Affected',
                  familyTotals.length.toString(),
                  Icons.category_outlined,
                  Colors.orange,
                ),
              ),
              const SizedBox(width: Spacing.level3),
              Expanded(
                child: _buildSummaryCard(
                  'Top Rejecting Environment',
                  topRejectingEnvironments.isNotEmpty
                      ? topRejectingEnvironments.first['environment_name']
                      : 'None',
                  Icons.computer_outlined,
                  Colors.blue,
                ),
              ),
            ],
          ),

          const SizedBox(height: Spacing.level5),

          // Time Series Chart
          if (timeSeries.isNotEmpty) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(Spacing.level4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Rejections Over Time',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: Spacing.level4),
                    SizedBox(
                      height: 300,
                      child: _buildTimeSeriesChart(timeSeries),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: Spacing.level5),
          ],

          // Summary Tables
          Row(
            children: [
              // Top Rejected Artefacts
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Spacing.level4),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Top Rejected Artefacts',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: Spacing.level3),
                        if (topRejectedArtefacts.isEmpty)
                          const Text('No rejections found')
                        else
                          ...topRejectedArtefacts.map(
                            (artefact) => ListTile(
                              dense: true,
                              leading: CircleAvatar(
                                radius: 12,
                                backgroundColor: _getFamilyColor(
                                  artefact['family'],
                                ),
                                child: Text(
                                  artefact['family'][0].toUpperCase(),
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                              title: Text(artefact['artefact_name']),
                              subtitle: Text(artefact['family']),
                              trailing: Text('${artefact['rejection_count']}'),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),

              const SizedBox(width: Spacing.level3),

              // Top Rejecting Environments
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Spacing.level4),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Top Rejecting Environments',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: Spacing.level3),
                        if (topRejectingEnvironments.isEmpty)
                          const Text('No rejections found')
                        else
                          ...topRejectingEnvironments.map(
                            (env) => ListTile(
                              dense: true,
                              leading: const Icon(Icons.computer, size: 24),
                              title: Text(env['environment_name']),
                              trailing: Text('${env['rejection_count']}'),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: Spacing.level5),

          // Detailed Rejections Table
          if (rejectionDetails.isNotEmpty) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(Spacing.level4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Recent Rejections',
                      style: Theme.of(context).textTheme.titleLarge,
                    ),
                    const SizedBox(height: Spacing.level3),
                    _buildRejectionsTable(rejectionDetails),
                  ],
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildSummaryCard(
    String title,
    String value,
    IconData icon,
    Color color,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(Spacing.level4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 24),
                const SizedBox(width: Spacing.level2),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: Spacing.level2),
            Text(
              value,
              style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildTimeSeriesChart(List<dynamic> timeSeries) {
    if (timeSeries.isEmpty) {
      return const Center(child: Text('No data available'));
    }

    final spots = <FlSpot>[];
    for (int i = 0; i < timeSeries.length; i++) {
      final item = timeSeries[i];
      final count = item['total_rejections'] as int;
      spots.add(FlSpot(i.toDouble(), count.toDouble()));
    }

    return LineChart(
      LineChartData(
        gridData: FlGridData(show: true),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              getTitlesWidget: (value, meta) => Text(
                value.toInt().toString(),
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 40,
              interval: (timeSeries.length / 7).ceilToDouble(),
              getTitlesWidget: (value, meta) {
                final index = value.toInt();
                if (index >= 0 && index < timeSeries.length) {
                  final date = DateTime.parse(timeSeries[index]['date']);
                  return Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      DateFormat.Md().format(date),
                      style: const TextStyle(fontSize: 10),
                    ),
                  );
                }
                return const Text('');
              },
            ),
          ),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        ),
        borderData: FlBorderData(show: true),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            color: Colors.red,
            barWidth: 3,
            dotData: FlDotData(show: true),
            belowBarData: BarAreaData(
              show: true,
              color: Colors.red.withValues(alpha: 0.1),
            ),
          ),
        ],
        minY: 0,
      ),
    );
  }

  Widget _buildRejectionsTable(List<dynamic> rejectionDetails) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columnSpacing: 20,
        columns: const [
          DataColumn(label: Text('Date')),
          DataColumn(label: Text('Family')),
          DataColumn(label: Text('Artefact')),
          DataColumn(label: Text('Version')),
          DataColumn(label: Text('Environment')),
          DataColumn(label: Text('Comment')),
        ],
        rows: rejectionDetails.take(50).map((rejection) {
          final date = DateTime.parse(rejection['timestamp']);
          return DataRow(
            cells: [
              DataCell(Text(DateFormat.yMMMd().add_Hms().format(date))),
              DataCell(
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: _getFamilyColor(
                      rejection['family'],
                    ).withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    rejection['family'],
                    style: TextStyle(
                      color: _getFamilyColor(rejection['family']),
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              DataCell(Text(rejection['artefact_name'])),
              DataCell(Text(rejection['artefact_version'])),
              DataCell(Text(rejection['environment_name'])),
              DataCell(
                Container(
                  constraints: const BoxConstraints(maxWidth: 200),
                  child: Text(
                    rejection['review_comment'] ?? 'No comment',
                    overflow: TextOverflow.ellipsis,
                    maxLines: 2,
                  ),
                ),
              ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Color _getFamilyColor(String family) {
    switch (family) {
      case 'snap':
        return Colors.green;
      case 'deb':
        return Colors.blue;
      case 'charm':
        return Colors.purple;
      case 'image':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}
