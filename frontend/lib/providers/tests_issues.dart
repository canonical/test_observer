import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_issue.dart';
import 'api.dart';

part 'tests_issues.g.dart';

@riverpod
Future<List<TestIssue>> testsIssues(TestsIssuesRef ref) {
  final api = ref.watch(apiProvider);
  return api.getTestIssues();
}
