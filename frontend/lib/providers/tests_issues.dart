import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_issue.dart';
import 'api.dart';

part 'tests_issues.g.dart';

@riverpod
class TestsIssues extends _$TestsIssues {
  @override
  Future<List<TestIssue>> build() {
    final api = ref.watch(apiProvider);
    return api.getTestIssues();
  }

  void updateIssue(TestIssue issue) async {
    final api = ref.read(apiProvider);
    final updatedIssue = await api.updateTestIssue(issue);
    final issues = await future;
    state = AsyncData([
      for (final issue in issues)
        issue.id == updatedIssue.id ? updatedIssue : issue,
    ]);
  }
}
