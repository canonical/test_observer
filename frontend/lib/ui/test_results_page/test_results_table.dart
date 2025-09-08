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

import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../models/detailed_test_results.dart';
import '../../models/test_result.dart';
import '../../models/test_execution.dart';
import '../../models/artefact.dart';
import '../../models/environment.dart';
import 'test_results_details_dialog.dart';
import 'test_results_helpers.dart';

class TestResultsTable extends StatelessWidget {
  final List<TestResultWithContext> testResults;
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
        final availableWidth = math.max(constraints.maxWidth, 1000.0);

        return SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: SizedBox(
            width: availableWidth,
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
          SizedBox(
            width: availableWidth * 0.15,
            child: _buildHeaderCell('Artefact'),
          ),
          SizedBox(
            width: availableWidth * 0.18,
            child: _buildHeaderCell('Test Case'),
          ),
          SizedBox(
            width: availableWidth * 0.10,
            child: _buildHeaderCell('Status'),
          ),
          SizedBox(
            width: availableWidth * 0.08,
            child: _buildHeaderCell('Track'),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildHeaderCell('Version'),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildHeaderCell('Environment'),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildHeaderCell('Test Plan'),
          ),
          SizedBox(
            width: availableWidth * 0.13,
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
    TestResultWithContext result,
    double availableWidth,
    int index,
  ) {
    final testResult = result.testResult;
    final testExecution = result.testExecution;
    final artefact = result.artefact;
    final artefactBuild = result.artefactBuild;
    final environment = testExecution.environment;

    return Container(
      width: availableWidth,
      constraints: const BoxConstraints(
        minHeight: 60,
      ),
      decoration: BoxDecoration(
        color: index.isEven ? Colors.white : Colors.grey[50],
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: availableWidth * 0.15,
            child: _buildArtefactCell(artefact),
          ),
          SizedBox(
            width: availableWidth * 0.18,
            child: _buildTestCaseCell(testResult),
          ),
          SizedBox(
            width: availableWidth * 0.10,
            child: _buildStatusCell(testResult.status),
          ),
          SizedBox(
            width: availableWidth * 0.08,
            child: _buildTrackCell(artefact),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildVersionCell(artefact),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildEnvironmentCell(artefactBuild, environment),
          ),
          SizedBox(
            width: availableWidth * 0.12,
            child: _buildTestPlanCell(testExecution),
          ),
          SizedBox(
            width: availableWidth * 0.13,
            child: _buildActionsCell(context, result),
          ),
        ],
      ),
    );
  }

  Widget _buildArtefactCell(Artefact artefact) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        artefact.name,
        style: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 14,
        ),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildTestCaseCell(TestResult testResult) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            testResult.name,
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 14,
            ),
            overflow: TextOverflow.ellipsis,
            maxLines: 2,
          ),
          if (testResult.category.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              testResult.category,
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

  Widget _buildStatusCell(TestResultStatus status) {
    final statusIcon = status.getIcon();

    return Container(
      padding: const EdgeInsets.all(12.0),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          statusIcon,
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              status.name.toUpperCase(),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTrackCell(Artefact artefact) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        artefact.track,
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildVersionCell(Artefact artefact) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        artefact.version,
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildEnvironmentCell(
    ArtefactBuildMinimal artefactBuild,
    Environment environment,
  ) {
    final architecture = artefactBuild.architecture;
    final environmentName = environment.name;
    final buildInfo = '$architecture/$environmentName';

    return Container(
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

  Widget _buildTestPlanCell(TestExecution testExecution) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        testExecution.testPlan.isNotEmpty ? testExecution.testPlan : 'Unknown',
        style: const TextStyle(fontSize: 14),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }

  Widget _buildActionsCell(BuildContext context, TestResultWithContext result) {
    return Container(
      padding: const EdgeInsets.all(8.0),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          InkWell(
            onTap: () => _showTestResultDetails(context, result),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.visibility, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text(
                    'Details',
                    style: TextStyle(
                      fontSize: 12,
                      color: YaruColors.orange,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 4),
          InkWell(
            onTap: () => _navigateToTestExecution(result),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.launch, size: 16, color: YaruColors.orange),
                  const SizedBox(width: 4),
                  Text(
                    'Run',
                    style: TextStyle(
                      fontSize: 12,
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
    TestResultWithContext result,
  ) {
    showDialog(
      context: context,
      builder: (context) => TestResultDetailsDialog(result: result),
    );
  }

  void _navigateToTestExecution(TestResultWithContext result) {
    TestResultHelpers.navigateToTestExecution(result);
  }
}
