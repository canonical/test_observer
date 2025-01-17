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

import '../../../models/test_issue.dart';
import '../../inline_url_text.dart';
import 'test_issue_form.dart';

class TestIssueListItem extends StatelessWidget {
  const TestIssueListItem({super.key, required this.issue});

  final TestIssue issue;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Tooltip(
        message: issue.description,
        child: Text(issue.description, overflow: TextOverflow.ellipsis),
      ),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          InlineUrlText(
            url: issue.url,
            urlText: 'URL',
            fontStyle: Theme.of(context).textTheme.bodyMedium,
          ),
          TextButton(
            onPressed: () =>
                showTestIssueUpdateDialog(context: context, issue: issue),
            child: const Text('edit'),
          ),
        ],
      ),
    );
  }
}
