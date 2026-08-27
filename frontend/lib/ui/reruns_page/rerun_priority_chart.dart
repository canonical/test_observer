// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../models/rerun_details.dart';
import '../spacing.dart';

/// Bar chart of rerun counts per priority.
///
/// Bars sit at sequential x indices and are labelled with the real (signed)
/// priority, so only priorities that actually have reruns are shown and they
/// are spaced evenly regardless of the numeric gaps between them.
class RerunPriorityChart extends StatelessWidget {
  const RerunPriorityChart({
    super.key,
    required this.summaries,
    required this.selectedPriority,
    required this.onBarTap,
  });

  final List<RerunPrioritySummary> summaries;
  final int? selectedPriority;
  final void Function(int priority) onBarTap;

  static const _barWidth = 28.0;
  static const _spacePerBar = 72.0;

  @override
  Widget build(BuildContext context) {
    final maxCount =
        summaries.map((s) => s.count).fold<int>(0, (a, b) => a > b ? a : b);
    final maxY = (maxCount + 1).toDouble();
    final rawInterval = (maxY / 5).ceilToDouble();
    final leftInterval = rawInterval < 1 ? 1.0 : rawInterval;

    return SizedBox(
      height: 320,
      child: LayoutBuilder(
        builder: (context, constraints) {
          final contentWidth = summaries.length * _spacePerBar;
          final width = contentWidth < constraints.maxWidth
              ? constraints.maxWidth
              : contentWidth;

          return SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: SizedBox(
              width: width,
              child: BarChart(
                BarChartData(
                  alignment: BarChartAlignment.spaceAround,
                  minY: 0,
                  maxY: maxY,
                  barTouchData: BarTouchData(
                    touchCallback: (event, response) {
                      if (event is! FlTapUpEvent) return;
                      final index = response?.spot?.touchedBarGroupIndex;
                      if (index != null &&
                          index >= 0 &&
                          index < summaries.length) {
                        onBarTap(summaries[index].priority);
                      }
                    },
                    touchTooltipData: BarTouchTooltipData(
                      getTooltipItem: (group, groupIndex, rod, rodIndex) {
                        final summary = summaries[group.x];
                        return BarTooltipItem(
                          'Priority ${summary.priority}\n'
                          '${summary.count} rerun(s)',
                          const TextStyle(color: Colors.white),
                        );
                      },
                    ),
                  ),
                  titlesData: FlTitlesData(
                    rightTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    topTitles: const AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    leftTitles: AxisTitles(
                      axisNameWidget: const Text('Number of reruns'),
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 40,
                        interval: leftInterval,
                        getTitlesWidget: (value, meta) {
                          if (value != value.roundToDouble()) {
                            return const SizedBox.shrink();
                          }
                          return Text(
                            '${value.toInt()}',
                            style: Theme.of(context).textTheme.bodySmall,
                          );
                        },
                      ),
                    ),
                    bottomTitles: AxisTitles(
                      axisNameWidget: const Text('Priority'),
                      sideTitles: SideTitles(
                        showTitles: true,
                        reservedSize: 32,
                        getTitlesWidget: (value, meta) {
                          final index = value.toInt();
                          if (index < 0 || index >= summaries.length) {
                            return const SizedBox.shrink();
                          }
                          return Padding(
                            padding: const EdgeInsets.only(top: Spacing.level2),
                            child: Text(
                              '${summaries[index].priority}',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                  gridData: const FlGridData(
                    show: true,
                    drawVerticalLine: false,
                  ),
                  borderData: FlBorderData(show: false),
                  barGroups: [
                    for (var i = 0; i < summaries.length; i++)
                      BarChartGroupData(
                        x: i,
                        barRods: [
                          BarChartRodData(
                            toY: summaries[i].count.toDouble(),
                            width: _barWidth,
                            color: summaries[i].priority == selectedPriority
                                ? YaruColors.orange
                                : Theme.of(context).colorScheme.primary,
                            borderRadius: const BorderRadius.vertical(
                              top: Radius.circular(4),
                            ),
                          ),
                        ],
                      ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
