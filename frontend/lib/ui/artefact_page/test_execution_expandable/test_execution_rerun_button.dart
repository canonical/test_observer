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

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../models/test_execution.dart';
import '../../../providers/artefact_builds.dart';
import '../../../routing.dart';
import '../../rerun_priority_form_field.dart';

class RerunButton extends ConsumerWidget {
  const RerunButton({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));

    if (testExecution.isRerunRequested) {
      return TextButton(
        onPressed: () => showDialog(
          context: context,
          builder: (_) => _ModifyRerunDialog(
            artefactId: artefactId,
            testExecutionId: testExecution.id,
            currentPriority: testExecution.rerunPriority,
          ),
        ),
        child: const Text('modify rerun'),
      );
    }

    return TextButton(
      onPressed: () => showDialog(
        context: context,
        builder: (_) => _RerunConfirmationDialog(
          artefactId: artefactId,
          testExecutionId: testExecution.id,
        ),
      ),
      child: const Text('rerun'),
    );
  }
}

class _RerunConfirmationDialog extends ConsumerStatefulWidget {
  const _RerunConfirmationDialog({
    required this.artefactId,
    required this.testExecutionId,
  });

  final int artefactId;
  final int testExecutionId;

  @override
  ConsumerState<_RerunConfirmationDialog> createState() =>
      _RerunConfirmationDialogState();
}

class _RerunConfirmationDialogState
    extends ConsumerState<_RerunConfirmationDialog> {
  final _formKey = GlobalKey<FormState>();
  final _priorityController = TextEditingController(text: '0');

  @override
  void dispose() {
    _priorityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text(
        'Are you sure you want to rerun this environment?',
      ),
      content: Form(
        key: _formKey,
        child: RerunPriorityFormField(controller: _priorityController),
      ),
      actions: [
        TextButton(
          autofocus: true,
          onPressed: () async {
            if (_formKey.currentState?.validate() != true) return;
            final priority = int.tryParse(_priorityController.text);
            final router = GoRouter.of(context);
            await ref
                .read(artefactBuildsProvider(widget.artefactId).notifier)
                .rerunTestExecutions(
              {widget.testExecutionId},
              priority: priority,
            );
            if (!mounted) return;
            router.pop();
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

class _ModifyRerunDialog extends ConsumerStatefulWidget {
  const _ModifyRerunDialog({
    required this.artefactId,
    required this.testExecutionId,
    required this.currentPriority,
  });

  final int artefactId;
  final int testExecutionId;
  final int? currentPriority;

  @override
  ConsumerState<_ModifyRerunDialog> createState() => _ModifyRerunDialogState();
}

class _ModifyRerunDialogState extends ConsumerState<_ModifyRerunDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _priorityController;

  @override
  void initState() {
    super.initState();
    _priorityController = TextEditingController(
      text: (widget.currentPriority ?? 0).toString(),
    );
  }

  @override
  void dispose() {
    _priorityController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Modify rerun request'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Warning: this rerun may have already been picked up or started.',
          ),
          const SizedBox(height: 16),
          Form(
            key: _formKey,
            child: RerunPriorityFormField(controller: _priorityController),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () async {
            if (_formKey.currentState?.validate() != true) return;
            final priority = int.tryParse(_priorityController.text);
            final router = GoRouter.of(context);
            await ref
                .read(artefactBuildsProvider(widget.artefactId).notifier)
                .rerunTestExecutions(
              {widget.testExecutionId},
              priority: priority,
            );
            if (!mounted) return;
            router.pop();
          },
          child: const Text('update priority'),
        ),
        TextButton(
          style: TextButton.styleFrom(foregroundColor: Colors.red),
          onPressed: () async {
            final router = GoRouter.of(context);
            await ref
                .read(artefactBuildsProvider(widget.artefactId).notifier)
                .deleteRerunTestExecutions({widget.testExecutionId});
            if (!mounted) return;
            router.pop();
          },
          child: const Text('delete rerun'),
        ),
        TextButton(
          autofocus: true,
          onPressed: () => context.pop(),
          child: const Text('cancel'),
        ),
      ],
    );
  }
}
