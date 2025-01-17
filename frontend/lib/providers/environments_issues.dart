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
