import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/environment.dart';
import '../../../providers/environments_issues.dart';
import '../../expandable.dart';
import 'environment_issue_form.dart';
import 'environment_issue_list_item.dart';

class EnvironmentIssuesExpandable extends ConsumerWidget {
  const EnvironmentIssuesExpandable({super.key, required this.environment});

  final Environment environment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref
            .watch(
              environmentsIssuesProvider.select(
                (value) => value.whenData(
                  (issues) => issues.filter(
                    (issue) => issue.environmentName == environment.name,
                  ),
                ),
              ),
            )
            .value ??
        [];

    return Expandable(
      initiallyExpanded: issues.isNotEmpty,
      title: Row(
        children: [
          Text('Reported Issues (${issues.length})'),
          const Spacer(),
          TextButton(
            onPressed: () => showEnvironmentIssueCreateDialog(
              context: context,
              environment: environment,
            ),
            child: const Text('add'),
          ),
        ],
      ),
      children: issues
          .map((issue) => EnvironmentIssueListItem(issue: issue))
          .toList(),
    );
  }
}
