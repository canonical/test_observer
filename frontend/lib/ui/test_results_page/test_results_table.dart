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
                const _TableHeader(),
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: testResults.length,
                  itemBuilder: (context, index) {
                    return _TableDataRow(
                      result: testResults[index],
                      index: index,
                    );
                  },
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _TableHeader extends StatelessWidget {
  const _TableHeader();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 56,
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(bottom: BorderSide(color: Colors.grey[300]!, width: 2)),
      ),
      child: const Row(
        children: [
          Expanded(flex: 3, child: _HeaderCell(title: 'Artefact')),
          Expanded(flex: 4, child: _HeaderCell(title: 'Test Case')),
          Expanded(flex: 3, child: _HeaderCell(title: 'Test Execution ID')),
          Expanded(flex: 2, child: _HeaderCell(title: 'Status')),
          Expanded(flex: 2, child: _HeaderCell(title: 'Track')),
          Expanded(flex: 3, child: _HeaderCell(title: 'Version')),
          Expanded(flex: 3, child: _HeaderCell(title: 'Environment')),
          Expanded(flex: 3, child: _HeaderCell(title: 'Test Plan')),
          Expanded(flex: 3, child: _HeaderCell(title: 'Actions')),
        ],
      ),
    );
  }
}

class _HeaderCell extends StatelessWidget {
  final String title;

  const _HeaderCell({required this.title});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        title,
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
  }
}

class _TableDataRow extends StatelessWidget {
  final TestResultWithContext result;
  final int index;

  const _TableDataRow({
    required this.result,
    required this.index,
  });

  @override
  Widget build(BuildContext context) {
    final testResult = result.testResult;
    final testExecution = result.testExecution;
    final artefact = result.artefact;
    final artefactBuild = result.artefactBuild;
    final environment = testExecution.environment;

    return Container(
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
          Expanded(flex: 3, child: _ArtefactCell(artefact: artefact)),
          Expanded(flex: 4, child: _TestCaseCell(testResult: testResult)),
          Expanded(flex: 3, child: _TestExecutionIDCell(testExecutionID: testExecution.id)),
          Expanded(flex: 2, child: _StatusCell(status: testResult.status)),
          Expanded(flex: 2, child: _TrackCell(artefact: artefact)),
          Expanded(flex: 3, child: _VersionCell(artefact: artefact)),
          Expanded(
            flex: 3,
            child: _EnvironmentCell(
              artefactBuild: artefactBuild,
              environment: environment,
            ),
          ),
          Expanded(flex: 3, child: _TestPlanCell(testExecution: testExecution)),
          Expanded(flex: 3, child: _ActionsCell(result: result)),
        ],
      ),
    );
  }
}

class _ArtefactCell extends StatelessWidget {
  final Artefact artefact;

  const _ArtefactCell({required this.artefact});

  @override
  Widget build(BuildContext context) {
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
}

class _TestCaseCell extends StatelessWidget {
  final TestResult testResult;

  const _TestCaseCell({required this.testResult});

  @override
  Widget build(BuildContext context) {
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
}

class _StatusCell extends StatelessWidget {
  final TestResultStatus status;

  const _StatusCell({required this.status});

  @override
  Widget build(BuildContext context) {
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
              maxLines: 1,
            ),
          ),
        ],
      ),
    );
  }
}

class _TrackCell extends StatelessWidget {
  final Artefact artefact;

  const _TrackCell({required this.artefact});

  @override
  Widget build(BuildContext context) {
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
}

class _VersionCell extends StatelessWidget {
  final Artefact artefact;

  const _VersionCell({required this.artefact});

  @override
  Widget build(BuildContext context) {
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
}

class _EnvironmentCell extends StatelessWidget {
  final ArtefactBuildMinimal artefactBuild;
  final Environment environment;

  const _EnvironmentCell({
    required this.artefactBuild,
    required this.environment,
  });

  @override
  Widget build(BuildContext context) {
    final architecture = artefactBuild.architecture;
    final environmentName = environment.name;
    final buildInfo = '$architecture/$environmentName';

    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Tooltip(
        message: buildInfo,
        child: Text(
          buildInfo,
          style: const TextStyle(fontSize: 14),
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
        ),
      ),
    );
  }
}

class _TestPlanCell extends StatelessWidget {
  final TestExecution testExecution;

  const _TestPlanCell({required this.testExecution});

  @override
  Widget build(BuildContext context) {
    final testPlan =
        testExecution.testPlan.isNotEmpty ? testExecution.testPlan : 'Unknown';

    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Tooltip(
        message: testPlan,
        child: Text(
          testPlan,
          style: const TextStyle(fontSize: 14),
          overflow: TextOverflow.ellipsis,
          maxLines: 1,
        ),
      ),
    );
  }
}

class _TestExecutionIDCell extends StatelessWidget {
  final int testExecutionID;

  const _TestExecutionIDCell({required this.testExecutionID});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12.0),
      alignment: Alignment.centerLeft,
      child: Text(
        testExecutionID.toString(),
        style: const TextStyle(
          fontWeight: FontWeight.w500,
          fontSize: 14,
        ),
      ),
    );
  }
}

class _ActionsCell extends StatelessWidget {
  final TestResultWithContext result;

  const _ActionsCell({required this.result});

  @override
  Widget build(BuildContext context) {
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
                    'View Run',
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
