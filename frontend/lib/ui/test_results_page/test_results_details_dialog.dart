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
import 'package:yaru/yaru.dart';

import '../../models/detailed_test_results.dart';
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
            _buildHeader(context),
            _buildContent(),
            _buildFooter(context),
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
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
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }

  Widget _buildContent() {
    return Expanded(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Test Case
            _buildSection(
              'Test Case',
              [
                _buildDetailRow('Name', result.testResult.name),
                _buildDetailRow('Category', result.testResult.category),
                _buildDetailRow('Template ID', result.testResult.templateId),
                _buildDetailRow('Status', result.testResult.status.name),
              ],
            ),

            const SizedBox(height: 16),

            // Artefact
            _buildSection(
              'Artefact',
              [
                _buildDetailRow(
                  'Family',
                  result.artefact.family.toUpperCase(),
                ),
                _buildDetailRow('Name', result.artefact.name),
                _buildDetailRow('Version', result.artefact.version),
                _buildDetailRow('Track', result.artefact.track),
                _buildDetailRow(
                  'Architecture',
                  result.artefactBuild.architecture,
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Execution
            _buildSection(
              'Test Execution',
              [
                _buildDetailRow(
                  'Execution ID',
                  result.testExecution.id.toString(),
                ),
                _buildDetailRow('Test Plan', result.testExecution.testPlan),
                _buildDetailRow(
                  'Environment',
                  result.testExecution.environment.name,
                ),
                _buildDetailRow('Status', result.testExecution.status.name),
                _buildDetailRow(
                  'Created',
                  result.testExecution.createdAt != null
                      ? TestResultHelpers.formatFullDate(
                          result.testExecution.createdAt!.toIso8601String(),
                        )
                      : 'N/A',
                ),
              ],
            ),

            // IO Log if present
            if (result.testResult.ioLog.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildSection(
                'IO Log',
                [
                  _buildLogContainer(result.testResult.ioLog),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildFooter(BuildContext context) {
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
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
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

  Widget _buildDetailRow(String label, String? value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              '$label:',
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.black87,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value ?? 'N/A',
              style: const TextStyle(color: Colors.black),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLogContainer(String logContent) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(4),
        border: Border.all(color: Colors.grey[300]!),
      ),
      child: Text(
        logContent,
        style: const TextStyle(
          fontFamily: 'monospace',
          fontSize: 12,
        ),
      ),
    );
  }
}
