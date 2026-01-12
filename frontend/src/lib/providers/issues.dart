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
import '../models/issue.dart';
import 'api.dart';

part 'issues.g.dart';

// Simple cache for Issue objects (not IssueWithContext)
// This allows us to display issues without fetching full context
@Riverpod(keepAlive: true)
class SimpleIssue extends _$SimpleIssue {
  @override
  Issue? build(int id) {
    // Return null initially - will be populated from search or fetched
    return null;
  }

  void setIssue(Issue issue) {
    state = issue;
  }

  Future<Issue> fetchIfNeeded() async {
    if (state != null) return state!;

    // Fetch from API if not in cache
    final api = ref.read(apiProvider);
    final issueWithContext = await api.getIssue(id);
    final issue = issueWithContext.toIssue();
    state = issue;
    return issue;
  }
}

@Riverpod(keepAlive: true)
class Issues extends _$Issues {
  @override
  Future<List<Issue>> build({
    String? source,
    String? project,
    int? limit,
    int? offset,
    String? q,
  }) async {
    final api = ref.watch(apiProvider);
    final issues = await api.getIssues(
      source: source,
      project: project,
      limit: limit,
      offset: offset,
      q: q,
    );

    // Populate the simple issue cache with these results
    for (final issue in issues) {
      ref.read(simpleIssueProvider(issue.id).notifier).setIssue(issue);
    }

    return issues;
  }

  Future<Issue> createIssue({
    required String url,
    String? title,
    String? status,
  }) async {
    final api = ref.read(apiProvider);
    final newIssue = await api.createIssue(
      url: url,
      title: title,
      status: status,
    );
    final issues = await future;
    final index = issues.indexWhere((issue) => issue.id == newIssue.id);
    List<Issue> updatedIssues;
    if (index != -1) {
      updatedIssues = List<Issue>.from(issues);
      updatedIssues[index] = newIssue;
    } else {
      updatedIssues = [...issues, newIssue];
    }
    state = AsyncData(updatedIssues);
    return newIssue;
  }
}
