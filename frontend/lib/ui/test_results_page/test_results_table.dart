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

import 'test_results_details_dialog.dart';
import 'test_results_helpers.dart';

class TestResultsTable extends StatelessWidget {
  final List<dynamic> testResults;
  final VoidCallback? onViewExecution;

  const TestResultsTable({
    super.key,
    required this.testResults,
    this.onViewExecution,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final availableWidth = constraints.maxWidth;

        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: ConstrainedBox(
            constraints: BoxConstraints(
              minWidth: availableWidth,
            ),
            child: DataTable(
              columnSpacing: 12,
              headingRowHeight: 56,
              dataRowMinHeight: 48,
              dataRowMaxHeight: 72,
              columns: const [
                DataColumn(
                  label: Text(
                    'Artefact',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Test Case',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Status',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Track',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Version',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Environment',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Test Plan',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                DataColumn(
                  label: Text(
                    'Actions',
                    style: TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
              ],
              rows: testResults.map((result) {
                final testResult =
                    result['test_result'] as Map<String, dynamic>;
                final testExecution =
                    result['test_execution'] as Map<String, dynamic>;
                final artefact = result['artefact'] as Map<String, dynamic>;
                final artefactBuild =
                    result['artefact_build'] as Map<String, dynamic>;
                final environment =
                    testExecution['environment'] as Map<String, dynamic>?;

                return DataRow(
                  cells: [
                    DataCell(_buildArtefactCell(artefact, availableWidth)),
                    DataCell(_buildTestCaseCell(testResult, availableWidth)),
                    DataCell(_buildStatusCell(testResult['status'])),
                    DataCell(_buildTrackCell(artefact, availableWidth)),
                    DataCell(_buildVersionCell(artefact, availableWidth)),
                    DataCell(
                      _buildEnvironmentCell(
                        artefactBuild,
                        environment,
                        availableWidth,
                      ),
                    ),
                    DataCell(_buildTestPlanCell(testExecution, availableWidth)),
                    DataCell(_buildActionsCell(context, result)),
                  ],
                );
              }).toList(),
            ),
          ),
        );
      },
    );
  }

  Widget _buildArtefactCell(
    Map<String, dynamic> artefact,
    double availableWidth,
  ) {
    final cellWidth = (availableWidth * 0.15).clamp(120.0, 200.0);

    return SizedBox(
      width: cellWidth,
      child: Text(
        artefact['name'] ?? 'Unknown',
        style: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 14,
        ),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildTestCaseCell(
    Map<String, dynamic> testResult,
    double availableWidth,
  ) {
    final cellWidth = (availableWidth * 0.18).clamp(180.0, 280.0);

    return SizedBox(
      width: cellWidth,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            testResult['name'] ?? 'Unknown',
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 14,
            ),
            overflow: TextOverflow.ellipsis,
            maxLines: 2,
          ),
          if (testResult['category'] != null) ...[
            const SizedBox(height: 2),
            Text(
              testResult['category'],
              style: TextStyle(
                fontSize: 12,
                color: Colors.grey[600],
              ),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusCell(String? status) {
    final testStatus = TestResultHelpers.parseTestResultStatus(status);
    final statusIcon = testStatus.getIcon();

    return SizedBox(
      width: 100,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          statusIcon,
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              testStatus.name.toUpperCase(),
              style: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTrackCell(Map<String, dynamic> artefact, double availableWidth) {
    final cellWidth = (availableWidth * 0.08).clamp(70.0, 100.0);

    return SizedBox(
      width: cellWidth,
      child: Text(
        artefact['track'] ?? 'Unknown',
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildVersionCell(
    Map<String, dynamic> artefact,
    double availableWidth,
  ) {
    final cellWidth = (availableWidth * 0.12).clamp(90.0, 140.0);

    return SizedBox(
      width: cellWidth,
      child: Text(
        artefact['version'] ?? 'Unknown',
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildEnvironmentCell(
    Map<String, dynamic> artefactBuild,
    Map<String, dynamic>? environment,
    double availableWidth,
  ) {
    final cellWidth = (availableWidth * 0.1).clamp(80.0, 120.0);

    final architecture = artefactBuild['architecture'] ?? 'unknown';
    final environmentName = environment?['name'] ?? 'unknown';
    final buildInfo = '$architecture/$environmentName';

    return SizedBox(
      width: cellWidth,
      child: Text(
        buildInfo,
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildTestPlanCell(
    Map<String, dynamic> testExecution,
    double availableWidth,
  ) {
    final cellWidth = (availableWidth * 0.12).clamp(120.0, 180.0);

    return SizedBox(
      width: cellWidth,
      child: Text(
        testExecution['test_plan'] ?? 'Unknown',
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildActionsCell(BuildContext context, Map<String, dynamic> result) {
    return SizedBox(
      width: 180,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          InkWell(
            onTap: () => _showTestResultDetails(context, result),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.visibility, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text(
                    'Details',
                    style: TextStyle(
                      fontSize: 14,
                      color: YaruColors.orange,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          InkWell(
            onTap: () => _navigateToTestExecution(result),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.launch, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text(
                    'Run',
                    style: TextStyle(
                      fontSize: 14,
                      color: YaruColors.orange,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showTestResultDetails(
    BuildContext context,
    Map<String, dynamic> result,
  ) {
    showDialog(
      context: context,
      builder: (context) => TestResultDetailsDialog(result: result),
    );
  }

  void _navigateToTestExecution(Map<String, dynamic> result) {
    TestResultHelpers.navigateToTestExecution(result);
  }
}
