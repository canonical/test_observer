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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'api.dart';

class TestSummaryParams {
  final DateRange? dateRange;
  final List<String> families;
  
  const TestSummaryParams({
    this.dateRange,
    required this.families,
  });
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is TestSummaryParams &&
        other.dateRange == dateRange &&
        other.families.length == families.length &&
        other.families.every((f) => families.contains(f));
  }
  
  @override
  int get hashCode => Object.hash(dateRange, Object.hashAll(families));
}

final testSummaryProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, TestSummaryParams>((ref, params) async {
  final api = ref.watch(apiProvider);
  
  // Use the optimized test summary endpoint instead of processing CSV
  final summaryData = await api.getTestSummaryReport(
    startDate: params.dateRange?.startDate,
    endDate: params.dateRange?.endDate,
    families: params.families,
  );
  
  return summaryData;
});


final knownIssuesReportProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, DateRange?>((ref, dateRange) async {
  final api = ref.watch(apiProvider);
  final issues = await api.getKnownIssuesReport(
    startDate: dateRange?.startDate,
    endDate: dateRange?.endDate,
  );
  return {
    'issues': issues,
    'total_count': issues.length,
  };
});

final environmentIssuesReportProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, DateRange?>((ref, dateRange) async {
  final api = ref.watch(apiProvider);
  final issues = await api.getEnvironmentsIssuesWithCounts(
    startDate: dateRange?.startDate,
    endDate: dateRange?.endDate,
  );
  return {
    'issues': issues,
    'total_count': issues.length,
  };
});

final testCaseIssuesProvider = FutureProvider.autoDispose.family<List<dynamic>, String>((ref, testIdentifier) async {
  final api = ref.watch(apiProvider);
  
  // Try to parse the test identifier to get template_id or case_name
  String? templateId;
  String? caseName;
  
  // If it contains "::" it's likely a template_id format
  if (testIdentifier.contains('::')) {
    templateId = testIdentifier;
  } else {
    caseName = testIdentifier;
  }
  
  final issues = await api.getKnownIssuesReport(
    templateId: templateId,
    caseName: caseName,
  );
  
  return issues;
});

// Simple direct provider for batch checking test case issues  
final batchTestCaseIssuesProvider = FutureProvider.autoDispose.family<Map<String, bool>, List<String>>((ref, testIdentifiers) async {
  if (testIdentifiers.isEmpty) return {};
  
  final api = ref.watch(apiProvider);
  return api.batchCheckTestCaseIssues(testIdentifiers);
});

final affectedArtefactsProvider = FutureProvider.autoDispose.family<dynamic, int>((ref, issueId) async {
  final api = ref.watch(apiProvider);
  return api.getAffectedArtefacts(issueId);
});

final testCaseAffectedArtefactsProvider = FutureProvider.family<Map<String, dynamic>, String>((ref, testIdentifier) async {
  final api = ref.watch(apiProvider);
  return api.getTestCaseAffectedArtefacts(testIdentifier);
});

class EnvironmentAffectedArtefactsParams {
  final int issueId;
  final DateRange? dateRange;
  
  const EnvironmentAffectedArtefactsParams({
    required this.issueId,
    this.dateRange,
  });
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is EnvironmentAffectedArtefactsParams &&
        other.issueId == issueId &&
        other.dateRange == dateRange;
  }
  
  @override
  int get hashCode => Object.hash(issueId, dateRange);
}

final environmentAffectedArtefactsProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, EnvironmentAffectedArtefactsParams>((ref, params) async {
  final api = ref.watch(apiProvider);
  return api.getEnvironmentAffectedArtefacts(
    params.issueId,
    startDate: params.dateRange?.startDate,
    endDate: params.dateRange?.endDate,
  );
});

class RejectionsParams {
  final DateRange? dateRange;
  final List<String> families;
  
  const RejectionsParams({
    this.dateRange,
    required this.families,
  });
  
  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is RejectionsParams &&
        other.dateRange == dateRange &&
        other.families.length == families.length &&
        other.families.every((f) => families.contains(f));
  }
  
  @override
  int get hashCode => Object.hash(dateRange, Object.hashAll(families));
}

final rejectionsReportProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, RejectionsParams>((ref, params) async {
  final api = ref.watch(apiProvider);
  
  return api.getRejectionsReport(
    startDate: params.dateRange?.startDate,
    endDate: params.dateRange?.endDate,
    families: params.families,
  );
});

final rejectionsSummaryProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, RejectionsParams>((ref, params) async {
  final api = ref.watch(apiProvider);
  
  return api.getRejectionsSummary(
    startDate: params.dateRange?.startDate,
    endDate: params.dateRange?.endDate,
    families: params.families,
  );
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