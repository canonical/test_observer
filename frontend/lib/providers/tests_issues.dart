// Copyright (C) 2023-2025 Canonical Ltd.
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

  void createIssue(
    String url,
    String description, {
    String? caseName,
    String? templateId,
  }) async {
    final api = ref.read(apiProvider);
    final issue =
        await api.createTestIssue(url, description, caseName, templateId);
    final issues = await future;
    state = AsyncData([...issues, issue]);
  }

  void deleteIssue(int issueId) async {
    final api = ref.read(apiProvider);
    await api.deleteTestIssue(issueId);
    final issues = await future;
    state = AsyncData([
      for (final issue in issues)
        if (issue.id != issueId) issue,
    ]);
  }
}
