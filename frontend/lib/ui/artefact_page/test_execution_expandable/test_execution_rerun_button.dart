// Copyright (C) 2024 Canonical Ltd.
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
import 'package:go_router/go_router.dart';

import '../../../models/test_execution.dart';
import '../../../providers/artefact_builds.dart';
import '../../../routing.dart';

class RerunButton extends ConsumerWidget {
  const RerunButton({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));

    final handlePress = testExecution.isRerunRequested
        ? null
        : () => showDialog(
              context: context,
              builder: (_) => _RerunConfirmationDialog(
                artefactId: artefactId,
                testExecutionId: testExecution.id,
              ),
            );

    return Tooltip(
      message: testExecution.isRerunRequested ? 'Already requested' : '',
      child: TextButton(
        onPressed: handlePress,
        child: const Text('rerun'),
      ),
    );
  }
}

class _RerunConfirmationDialog extends ConsumerWidget {
  const _RerunConfirmationDialog({
    required this.artefactId,
    required this.testExecutionId,
  });

  final int artefactId;
  final int testExecutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AlertDialog(
      title: const Text(
        'Are you sure you want to rerun this environment?',
      ),
      actions: [
        TextButton(
          autofocus: true,
          onPressed: () {
            ref
                .read(artefactBuildsProvider(artefactId).notifier)
                .rerunTestExecutions({testExecutionId});
            context.pop();
          },
          child: const Text('yes'),
        ),
        TextButton(
          onPressed: () => context.pop(),
          child: const Text('no'),
        ),
      ],
    );
  }
}
