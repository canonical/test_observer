import 'package:flutter/material.dart';

import '../../../models/environment_issue.dart';
import '../../inline_url_text.dart';
import 'environment_issue_form.dart';

class EnvironmentIssueListItem extends StatelessWidget {
  const EnvironmentIssueListItem({super.key, required this.issue});

  final EnvironmentIssue issue;

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
            onPressed: () => showEnvironmentIssueUpdateDialog(
              context: context,
              issue: issue,
            ),
            child: const Text('edit'),
          ),
        ],
      ),
    );
  }
}
