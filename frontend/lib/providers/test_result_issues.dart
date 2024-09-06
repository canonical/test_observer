import 'package:dartx/dartx.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_issue.dart';
import '../models/test_result.dart';
import 'tests_issues.dart';

part 'test_result_issues.g.dart';

@riverpod
Future<List<TestIssue>> testResultIssues(
  TestResultIssuesRef ref,
  TestResult testResult,
) {
  return ref.watch(
    testsIssuesProvider.selectAsync(
      (issues) => issues
          .filter(
            (issue) =>
                issue.caseName == testResult.name ||
                issue.templateId == testResult.templateId,
          )
          .toList(),
    ),
  );
}
