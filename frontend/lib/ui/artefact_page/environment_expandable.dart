// Copyright 2024 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/artefact_environment.dart';
import '../../providers/selected_environments.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'environment_issues/environment_issues_expandable.dart';
import 'environment_review_button.dart';
import 'test_plan_expandable.dart';

class EnvironmentExpandable extends ConsumerWidget {
  const EnvironmentExpandable({
    super.key,
    required this.artefactId,
    required this.artefactEnvironment,
  });

  final int artefactId;
  final ArtefactEnvironment artefactEnvironment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final groupedTestExecutions =
        artefactEnvironment.runsDescending.groupBy((te) => te.testPlan);

    final pageUri = AppRoutes.uriFromContext(context);
    final targetTestExecutionId = pageUri.queryParameters['testExecutionId'];
    final shouldExpand = targetTestExecutionId != null &&
        artefactEnvironment.runsDescending
            .any((te) => te.id == int.tryParse(targetTestExecutionId));

    return Expandable(
      initiallyExpanded: shouldExpand,
      title: _EnvironmentExpandableTitle(
        artefactEnvironment: artefactEnvironment,
      ),
      children: [
        EnvironmentIssuesExpandable(
          environment: artefactEnvironment.environment,
        ),
        Expandable(
          title: const Text('Test Plans'),
          initiallyExpanded: true,
          children: groupedTestExecutions.values
              .map(
                (testExecutions) => TestPlanExpandable(
                  artefactId: artefactId,
                  initiallyExpanded: groupedTestExecutions.length == 1,
                  testExecutionsDescending: testExecutions,
                ),
              )
              .toList(),
        ),
      ],
    );
  }
}

class _EnvironmentExpandableTitle extends ConsumerWidget {
  const _EnvironmentExpandableTitle({required this.artefactEnvironment});

  final ArtefactEnvironment artefactEnvironment;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isSelected = ref.watch(
      selectedEnvironmentsProvider.select(
        (selected) => selected.contains(artefactEnvironment.environment.id),
      ),
    );

    return Row(
      children: [
        Checkbox(
          value: isSelected,
          onChanged: (value) {
            ref
                .read(selectedEnvironmentsProvider.notifier)
                .toggle(artefactEnvironment.environment.id);
          },
        ),
        const SizedBox(width: Spacing.level2),
        artefactEnvironment.runsDescending.first.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          artefactEnvironment.architecture,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(width: Spacing.level4),
        Text(
          artefactEnvironment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        EnvironmentReviewButton(environmentReview: artefactEnvironment.review),
      ],
    );
  }
}
