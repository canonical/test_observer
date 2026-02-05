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
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../models/detailed_test_results.dart';
import '../execution_metadata.dart';
import '../date_time.dart';
import 'test_results_helpers.dart';

class TestResultDetailsDialog extends StatelessWidget {
  final TestResultWithContext result;

  const TestResultDetailsDialog({
    super.key,
    required this.result,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 900, maxHeight: 1000),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            _DialogHeader(onClose: () => context.pop()),
            _DialogContent(result: result),
            _DialogFooter(onClose: () => context.pop(), result: result),
          ],
        ),
      ),
    );
  }
}

class _DialogHeader extends StatelessWidget {
  final VoidCallback onClose;

  const _DialogHeader({required this.onClose});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        color: YaruColors.orange,
        borderRadius: BorderRadius.only(
          topLeft: Radius.circular(4),
          topRight: Radius.circular(4),
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.info_outline, color: Colors.white),
          const SizedBox(width: 8),
          const Text(
            'Test Result Details',
            style: TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const Spacer(),
          IconButton(
            icon: const Icon(Icons.close, color: Colors.white),
            onPressed: onClose,
          ),
        ],
      ),
    );
  }
}

class _DialogContent extends StatelessWidget {
  final TestResultWithContext result;

  const _DialogContent({required this.result});

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Test Case
            _DialogSection(
              title: 'Test Case',
              children: [
                _DetailRow(label: 'Name', value: result.testResult.name),
                _DetailRow(
                  label: 'Category',
                  value: result.testResult.category,
                ),
                _DetailRow(
                  label: 'Template ID',
                  value: result.testResult.templateId,
                ),
                _DetailRow(
                  label: 'Status',
                  value: result.testResult.status.name,
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Artefact
            _DialogSection(
              title: 'Artefact',
              children: [
                _DetailRow(
                  label: 'Family',
                  value: result.artefact.family.toUpperCase(),
                ),
                _DetailRow(label: 'Name', value: result.artefact.name),
                _DetailRow(label: 'Version', value: result.artefact.version),
                _DetailRow(label: 'Track', value: result.artefact.track),
                _DetailRow(
                  label: 'Architecture',
                  value: result.artefactBuild.architecture,
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Execution
            _DialogSection(
              title: 'Test Execution',
              children: [
                _DetailRow(
                  label: 'Execution ID',
                  value: result.testExecution.id.toString(),
                ),
                _DetailRow(
                  label: 'Test Plan',
                  value: result.testExecution.testPlan,
                ),
                _DetailRow(
                  label: 'Environment',
                  value: result.testExecution.environment.name,
                ),
                _DetailRow(
                  label: 'Status',
                  value: result.testExecution.status.name,
                ),
                _DetailRow(
                  label: 'Created',
                  value: formatDateTime(result.testExecution.createdAt),
                ),
                _DetailRow(
                  label: 'Execution Metadata',
                  valueWidget: ExecutionMetadataTable(
                    metadata: result.testExecution.executionMetadata,
                  ),
                ),
              ],
            ),

            // IO Log if present
            if (result.testResult.ioLog.isNotEmpty) ...[
              const SizedBox(height: 16),
              _DialogSection(
                title: 'IO Log',
                children: [
                  _LogContainer(logContent: result.testResult.ioLog),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _DialogFooter extends StatelessWidget {
  final VoidCallback onClose;
  final TestResultWithContext result;

  const _DialogFooter({required this.onClose, required this.result});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(4),
          bottomRight: Radius.circular(4),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          InkWell(
            onTap: () => TestResultHelpers.navigateToTestExecution(result),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.launch, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text('View Run'),
                ],
              ),
            ),
          ),
          const SizedBox(width: 4),
          TextButton(
            onPressed: onClose,
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}

class _DialogSection extends StatelessWidget {
  final String title;
  final List<Widget> children;

  const _DialogSection({
    required this.title,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SelectableText(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: YaruColors.orange,
          ),
        ),
        const SizedBox(height: 8),
        ...children,
      ],
    );
  }
}

class _DetailRow extends StatelessWidget {
  final String label;
  final String? value;
  final Widget? valueWidget;

  const _DetailRow({
    required this.label,
    this.value,
    this.valueWidget,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 200,
            child: SelectableText(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
            ),
          ),
          Expanded(
            child: valueWidget ??
                SelectableText(
                  value ?? 'N/A',
                  style: const TextStyle(color: Colors.black),
                ),
          ),
        ],
      ),
    );
  }
}

class _LogContainer extends StatelessWidget {
  final String logContent;

  const _LogContainer({required this.logContent});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: SelectableText(
        logContent,
        style: const TextStyle(
          fontFamily: 'UbuntuMono',
          fontSize: 12,
        ),
      ),
    );
  }
}
