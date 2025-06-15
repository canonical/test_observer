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

import 'package:csv/csv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api.dart';

final testSummaryProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, DateRange?>((ref, dateRange) async {
  final api = ref.watch(apiProvider);
  final csvData = await api.getTestResultsCsv(
    startDate: dateRange?.startDate,
    endDate: dateRange?.endDate,
  );
  
  return _processTestResultsCsv(csvData, dateRange?.startDate, dateRange?.endDate);
});


final knownIssuesReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiProvider);
  final issues = await api.getKnownIssuesReport();
  return {
    'issues': issues,
    'total_count': issues.length,
  };
});

final environmentIssuesReportProvider = FutureProvider.autoDispose<Map<String, dynamic>>((ref) async {
  final api = ref.watch(apiProvider);
  final issues = await api.getEnvironmentsIssues();
  return {
    'issues': issues,
    'total_count': issues.length,
  };
});

class DateRange {
  final DateTime? startDate;
  final DateTime? endDate;
  
  const DateRange({this.startDate, this.endDate});
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is DateRange &&
        other.startDate == startDate &&
        other.endDate == endDate;
  }
  
  @override
  int get hashCode => Object.hash(startDate, endDate);
}

Map<String, dynamic> _processTestResultsCsv(String csvData, DateTime? startDate, DateTime? endDate) {
  final rows = const CsvToListConverter().convert(csvData);
  if (rows.isEmpty) {
    return {
      'start_date': startDate?.toIso8601String() ?? '0001-01-01T00:00:00',
      'end_date': endDate?.toIso8601String() ?? DateTime.now().toIso8601String(),
      'total_tests': 0,
      'total_executions': 0,
      'summary': <Map<String, dynamic>>[],
    };
  }

  final headers = rows.first.cast<String>();
  final dataRows = rows.skip(1);
  
  // Find column indices
  final familyIndex = headers.indexOf('Artefact.family');
  final templateIdIndex = headers.indexOf('TestCase.template_id');
  final nameIndex = headers.indexOf('TestCase.name');
  final statusIndex = headers.indexOf('TestResult.status');
  
  // Process data similar to fetch_test_results_report.py
  final testSummary = <String, Map<String, int>>{};
  int totalExecutions = 0;
  
  for (final row in dataRows) {
    if (row.length <= maxOf([familyIndex, templateIdIndex, nameIndex, statusIndex])) continue;
    
    final family = row[familyIndex]?.toString() ?? '';
    final templateId = row[templateIdIndex]?.toString() ?? '';
    final name = row[nameIndex]?.toString() ?? '';
    final status = row[statusIndex]?.toString() ?? '';
    
    // Filter like the script: only snap/deb, exclude mir tests
    if (!['snap', 'deb'].contains(family) || name.contains('mir')) {
      continue;
    }
    
    final testIdentifier = templateId.isNotEmpty ? templateId : name;
    testSummary.putIfAbsent(testIdentifier, () => {'FAILED': 0, 'PASSED': 0, 'SKIPPED': 0});
    testSummary[testIdentifier]![status] = (testSummary[testIdentifier]![status] ?? 0) + 1;
    totalExecutions++;
  }
  
  // Convert to summary format
  final summaryItems = testSummary.entries.map((entry) {
    final counts = entry.value;
    return {
      'test_identifier': entry.key,
      'total': (counts['FAILED'] ?? 0) + (counts['PASSED'] ?? 0),
      'failed': counts['FAILED'] ?? 0,
      'passed': counts['PASSED'] ?? 0,
      'skipped': counts['SKIPPED'] ?? 0,
    };
  }).toList();
  
  // Sort by total count descending
  summaryItems.sort((a, b) => (b['total'] as int).compareTo(a['total'] as int));
  
  return {
    'start_date': startDate?.toIso8601String() ?? '0001-01-01T00:00:00',
    'end_date': endDate?.toIso8601String() ?? DateTime.now().toIso8601String(),
    'total_tests': summaryItems.length,
    'total_executions': totalExecutions,
    'summary': summaryItems,
  };
}

int maxOf(List<int> values) {
  return values.reduce((a, b) => a > b ? a : b);
}