// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../models/test_result.dart';
import '../../providers/api.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/current_user.dart';
import '../spacing.dart';

class AddTestResultDialog extends ConsumerStatefulWidget {
  const AddTestResultDialog({
    super.key,
    required this.testExecutionId,
    required this.artefactId,
  });

  final int testExecutionId;
  final int artefactId;

  @override
  ConsumerState<AddTestResultDialog> createState() =>
      _AddTestResultDialogState();
}

class _AddTestResultDialogState extends ConsumerState<AddTestResultDialog> {
  final _formKey = GlobalKey<FormState>();
  final _testNameController = TextEditingController();
  final _commentController = TextEditingController();
  final _ioLogController = TextEditingController();
  TestResultStatus _selectedStatus = TestResultStatus.passed;
  bool _isSubmitting = false;

  String _testNamePrefix() {
    final user = ref.read(currentUserProvider).valueOrNull;
    final username = user?.launchpadHandle?.trim() ?? '';
    return username.isEmpty ? '' : '$username - ';
  }

  @override
  void dispose() {
    _testNameController.dispose();
    _commentController.dispose();
    _ioLogController.dispose();
    super.dispose();
  }

  Future<void> _handleSubmit() async {
    if (!_formKey.currentState!.validate() || _isSubmitting) {
      return;
    }

    setState(() => _isSubmitting = true);

    try {
      final api = ref.read(apiProvider);
      final prefix = _testNamePrefix();
      final rawTestName = _testNameController.text.trim();
      final testName =
          rawTestName.startsWith(prefix) ? rawTestName : '$prefix$rawTestName';

      await api.submitTestResult(
        testExecutionId: widget.testExecutionId,
        testName: testName,
        status: _selectedStatus,
        comment: _commentController.text.trim(),
        ioLog: _ioLogController.text.trim(),
      );

      // Invalidate the artefact builds to refresh the page
      if (mounted) {
        ref.invalidate(artefactBuildsProvider(widget.artefactId));
        context.pop();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Test result submitted successfully'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isSubmitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to submit test result: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final prefix = _testNamePrefix();

    return AlertDialog(
      scrollable: true,
      title: const Text('Add Test Result'),
      content: Form(
        key: _formKey,
        child: SizedBox(
          width: 500,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Add a test result to this test execution',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: Spacing.level3),
              // Test name
              TextFormField(
                controller: _testNameController,
                decoration: InputDecoration(
                  labelText: 'Test Name *',
                  hintText: 'e.g., test_login, camera/detect',
                  border: OutlineInputBorder(),
                  prefixText: prefix,
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Test name is required';
                  }
                  return null;
                },
              ),
              const SizedBox(height: Spacing.level4),
              // Status dropdown
              DropdownButtonFormField<TestResultStatus>(
                value: _selectedStatus,
                decoration: const InputDecoration(
                  labelText: 'Status *',
                  border: OutlineInputBorder(),
                ),
                items: TestResultStatus.values.map((status) {
                  return DropdownMenuItem(
                    value: status,
                    child: Row(
                      children: [
                        status.getIcon(),
                        const SizedBox(width: Spacing.level2),
                        Text(status.name),
                      ],
                    ),
                  );
                }).toList(),
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _selectedStatus = value);
                  }
                },
              ),
              const SizedBox(height: Spacing.level4),
              // Comment (optional)
              TextFormField(
                controller: _commentController,
                decoration: const InputDecoration(
                  labelText: 'Comment',
                  hintText: 'Additional notes about this test result',
                  border: OutlineInputBorder(),
                ),
                maxLines: 3,
              ),
              const SizedBox(height: Spacing.level4),
              // IO Log (optional)
              TextFormField(
                controller: _ioLogController,
                decoration: const InputDecoration(
                  labelText: 'Relevant Logs',
                  hintText: 'Test result logs',
                  border: OutlineInputBorder(),
                ),
                maxLines: 5,
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isSubmitting ? null : () => context.pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isSubmitting ? null : _handleSubmit,
          child: _isSubmitting
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Submit Test Result'),
        ),
      ],
    );
  }
}
