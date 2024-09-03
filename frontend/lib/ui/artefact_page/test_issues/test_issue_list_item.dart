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
                showTestIssueDialog(context: context, issueId: issue.id),
            child: const Text('edit'),
          ),
        ],
      ),
    );
  }
}
