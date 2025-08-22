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
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildHeader(availableWidth),
                SizedBox(
                  width: availableWidth,
                  height: (testResults.length * 72.0).clamp(200.0, 950.0),
                  child: ListView.builder(
                    itemCount: testResults.length,
                    itemBuilder: (context, index) {
                      return _buildDataRow(
                        context,
                        testResults[index],
                        availableWidth,
                        index,
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildHeader(double availableWidth) {
    return Container(
      width: availableWidth,
      height: 56,
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(bottom: BorderSide(color: Colors.grey[300]!, width: 2)),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 15,
            child: _buildHeaderCell('Artefact'),
          ),
          Expanded(
            flex: 18,
            child: _buildHeaderCell('Test Case'),
          ),
          Expanded(
            flex: 10,
            child: _buildHeaderCell('Status'),
          ),
          Expanded(
            flex: 8,
            child: _buildHeaderCell('Track'),
          ),
          Expanded(
            flex: 12,
            child: _buildHeaderCell('Version'),
          ),
          Expanded(
            flex: 10,
            child: _buildHeaderCell('Environment'),
          ),
          Expanded(
            flex: 12,
            child: _buildHeaderCell('Test Plan'),
          ),
          Expanded(
            flex: 15,
            child: _buildHeaderCell('Actions'),
          ),
        ],
      ),
    );
  }

  Widget _buildHeaderCell(String title) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildDataRow(
    BuildContext context,
    dynamic result,
    double availableWidth,
    int index,
  ) {
    final testResult = result['test_result'] as Map<String, dynamic>;
    final testExecution = result['test_execution'] as Map<String, dynamic>;
    final artefact = result['artefact'] as Map<String, dynamic>;
    final artefactBuild = result['artefact_build'] as Map<String, dynamic>;
    final environment = testExecution['environment'] as Map<String, dynamic>?;

    return Container(
      width: availableWidth,
      constraints: const BoxConstraints(
        minHeight: 48,
        maxHeight: 72,
      ),
      decoration: BoxDecoration(
        color: index.isEven ? Colors.white : Colors.grey[50],
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 15,
            child: _buildArtefactCell(artefact, availableWidth),
          ),
          Expanded(
            flex: 18,
            child: _buildTestCaseCell(testResult, availableWidth),
          ),
          Expanded(
            flex: 10,
            child: _buildStatusCell(testResult['status']),
          ),
          Expanded(
            flex: 8,
            child: _buildTrackCell(artefact, availableWidth),
          ),
          Expanded(
            flex: 12,
            child: _buildVersionCell(artefact, availableWidth),
          ),
          Expanded(
            flex: 10,
            child: _buildEnvironmentCell(
              artefactBuild,
              environment,
              availableWidth,
            ),
          ),
          Expanded(
            flex: 12,
            child: _buildTestPlanCell(testExecution, availableWidth),
          ),
          Expanded(
            flex: 15,
            child: _buildActionsCell(context, result),
          ),
        ],
      ),
    );
  }

  Widget _buildArtefactCell(
    Map<String, dynamic> artefact,
    double availableWidth,
  ) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
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
    return Container(
      padding: const EdgeInsets.all(12.0),
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

    return Container(
      padding: const EdgeInsets.all(12.0),
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

    return Container(
      width: cellWidth,
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
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

    return Container(
      width: cellWidth,
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
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
    final cellWidth = (availableWidth * 0.10).clamp(80.0, 120.0);
    final architecture = artefactBuild['architecture'] ?? 'unknown';
    final environmentName = environment?['name'] ?? 'unknown';
    final buildInfo = '$architecture/$environmentName';

    return Container(
      width: cellWidth,
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
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

    return Container(
      width: cellWidth,
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        testExecution['test_plan'] ?? 'Unknown',
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildActionsCell(BuildContext context, dynamic result) {
    return Container(
      width: 180,
      padding: const EdgeInsets.all(8.0),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          InkWell(
            onTap: () => _showTestResultDetails(context, result),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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
            onTap: () => TestResultHelpers.navigateToTestExecution(result),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
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

  void _showTestResultDetails(BuildContext context, dynamic result) {
    showDialog(
      context: context,
      builder: (context) => TestResultDetailsDialog(result: result),
    );
  }
}
