import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/environment_issue.dart';
import 'api.dart';

part 'environments_issues.g.dart';

@riverpod
class EnvironmentsIssues extends _$EnvironmentsIssues {
  @override
  Future<List<EnvironmentIssue>> build() {
    final api = ref.watch(apiProvider);
    return api.getEnvironmentsIssues();
  }

  Future<void> updateIssue(EnvironmentIssue issue) async {
    final api = ref.read(apiProvider);
    final updatedIssue = await api.updateEnvironmentIssue(issue);
    final issues = await future;
    state = AsyncData([
      for (final issue in issues)
        issue.id == updatedIssue.id ? updatedIssue : issue,
    ]);
  }

  Future<void> createIssue(
    String url,
    String description,
    String environmentName,
    bool isConfirmed,
  ) async {
    final api = ref.read(apiProvider);
    final issue = await api.createEnvironmentIssue(
      url,
      description,
      environmentName,
      isConfirmed,
    );
    final issues = await future;
    state = AsyncData([...issues, issue]);
  }

  Future<void> deleteIssue(int issueId) async {
    final api = ref.read(apiProvider);
    await api.deleteEnvironmentIssue(issueId);
    final issues = await future;
    state = AsyncData([
      for (final issue in issues)
        if (issue.id != issueId) issue,
    ]);
  }
}
