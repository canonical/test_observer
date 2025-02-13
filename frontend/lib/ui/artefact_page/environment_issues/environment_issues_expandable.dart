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

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/environment.dart';
import '../../../providers/environments_issues.dart';
import '../../expandable.dart';
import '../../vanilla/vanilla_button.dart';
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
          Text('Reported Environment Issues (${issues.length})'),
          const Spacer(),
          VanillaButton(
            type: VanillaButtonType.base,
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
