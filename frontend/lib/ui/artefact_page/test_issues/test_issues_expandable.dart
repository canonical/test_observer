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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/test_result.dart';
import '../../../providers/test_result_issues.dart';
import '../../expandable.dart';
import 'test_issue_form.dart';
import 'test_issue_list_item.dart';

class TestIssuesExpandable extends ConsumerWidget {
  const TestIssuesExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    return Expandable(
      initiallyExpanded: issues.isNotEmpty,
      title: Row(
        children: [
          Text('Reported Test Issues (${issues.length})'),
          const Spacer(),
          TextButton(
            onPressed: () => showTestIssueCreateDialog(
              context: context,
              testResult: testResult,
            ),
            child: const Text('add'),
          ),
        ],
      ),
      children: issues.map((issue) => TestIssueListItem(issue: issue)).toList(),
    );
  }
}
