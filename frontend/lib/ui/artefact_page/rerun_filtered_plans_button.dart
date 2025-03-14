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

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/filtered_enriched_test_executions.dart';
import '../../routing.dart';
import '../spacing.dart';

class RerunFilteredPlansButton extends ConsumerWidget {
  const RerunFilteredPlansButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final artefactId = AppRoutes.artefactIdFromUri(pageUri);
    final filteredEnrichedExecutions =
        ref.watch(filteredEnrichedTestExecutionsProvider(pageUri)).value ?? [];
    final groupedExecutions = filteredEnrichedExecutions.groupBy(
      (ee) => (
        ee.testExecution.artefactBuildId,
        ee.testExecution.environment.id,
        ee.testExecution.testPlan
      ),
    );
    final testExecutionsToRerun = groupedExecutions.values
        .map((group) => group.maxBy((ee) => ee.testExecution.id)!.testExecution)
        .toList();

    return TextButton(
      onPressed: () => showDialog(
        context: context,
        builder: (_) => _ConfirmationDialog(
          testExecutionsToRerun: testExecutionsToRerun,
          artefactId: artefactId,
        ),
      ),
      child: Text(
        'Rerun ${testExecutionsToRerun.length} Filtered Test Plans',
        textScaler: const TextScaler.linear(1.2),
      ),
    );
  }
}

class _ConfirmationDialog extends ConsumerWidget {
  const _ConfirmationDialog({
    required this.testExecutionsToRerun,
    required this.artefactId,
  });

  final List<TestExecution> testExecutionsToRerun;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    handleYes() {
      final testExecutionIds = {for (final te in testExecutionsToRerun) te.id};
      ref
          .read(artefactBuildsProvider(artefactId).notifier)
          .rerunTestExecutions(testExecutionIds);
      context.pop();
    }

    return AlertDialog(
      scrollable: true,
      title: Text(
        'Are you sure you want to rerun the following'
        ' ${testExecutionsToRerun.length} environments?',
      ),
      content: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: testExecutionsToRerun
            .map<Widget>((te) => Text(te.environment.name))
            .intersperse(const SizedBox(height: Spacing.level2))
            .toList(),
      ),
      actions: [
        TextButton(
          onPressed: handleYes,
          child: const Text('yes'),
        ),
        TextButton(
          autofocus: true,
          onPressed: () => context.pop(),
          child: const Text('no'),
        ),
      ],
    );
  }
}
