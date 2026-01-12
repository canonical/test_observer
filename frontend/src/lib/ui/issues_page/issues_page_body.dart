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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import '../../models/issue.dart';
import '../../routing.dart';
import '../spacing.dart';
import '../../providers/filtered_issues.dart';
import '../issues.dart';

class IssuesPageBody extends ConsumerWidget {
  const IssuesPageBody({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref
            .watch(filteredIssuesProvider(AppRoutes.uriFromContext(context)))
            .value ??
        [];

    // Group issues by named tuple (source, project)
    final grouped = <({IssueSource source, String project}), List<Issue>>{};
    for (var issue in issues) {
      final key = (source: issue.source, project: issue.project);
      grouped.putIfAbsent(key, () => []);
      grouped[key]!.add(issue);
    }

    if (grouped.isEmpty) {
      return const Center(child: Text('No issues found.'));
    }

    return ListView(
      children: [
        for (final entry in grouped.entries) ...[
          Padding(
            padding: const EdgeInsets.symmetric(
              vertical: Spacing.level4,
              horizontal: Spacing.level3,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              spacing: Spacing.level3,
              children: [
                IssueSourceWidget(
                  source: entry.key.source,
                  textStyle: Theme.of(context).textTheme.labelLarge,
                ),
                IssueProjectWidget(
                  project: entry.key.project,
                  textStyle: Theme.of(context).textTheme.bodyLarge,
                ),
              ],
            ),
          ),
          for (final issue in entry.value)
            ListTile(
              title: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                spacing: Spacing.level3,
                children: [
                  Row(
                    spacing: Spacing.level3,
                    children: [
                      IssueLinkWidget(issue: issue),
                      IssueStatusWidget(issue: issue),
                    ],
                  ),
                  IssueTitleWidget(issue: issue),
                ],
              ),
              onTap: () {
                navigateToIssuePage(context, issue.id);
              },
            ),
        ],
      ],
    );
  }
}
