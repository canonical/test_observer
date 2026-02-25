// Copyright 2025 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../providers/issue.dart';
import '../spacing.dart';
import 'issue_page_header.dart';
import 'test_results.dart';
import 'attachment_rules.dart';

class IssuePage extends ConsumerWidget {
  const IssuePage({super.key, required this.issueId});

  final int issueId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issueAsync = ref.watch(issueProvider(issueId));

    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: issueAsync.when(
        data: (issue) => SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              IssuePageHeader(issue: issue.toIssue()),
              SizedBox(height: Spacing.level4),
              AttachmentRulesSection(
                issueId: issue.id,
                attachmentRules: issue.attachmentRules,
              ),
              SizedBox(height: Spacing.level4),
              TestResultsSection(issue: issue.toIssue()),
            ],
          ),
        ),
        loading: () => const Center(child: YaruCircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Text('Error loading issue: $error'),
        ),
      ),
    );
  }
}
