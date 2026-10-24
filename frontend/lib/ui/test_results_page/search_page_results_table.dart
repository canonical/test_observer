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

import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:yaru/yaru.dart';

import '../../models/search_page_results.dart';
import '../../models/test_result.dart';
import 'search_page_results_navigation.dart';
import 'test_results_details_dialog.dart';

class SearchPageResultsTable extends StatelessWidget {
  const SearchPageResultsTable({super.key, required this.testResults});

  final List<SearchPageTableRow> testResults;

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
                const _SearchTableHeader(),
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: testResults.length,
                  itemBuilder:
                      (context, index) => _SearchTableRow(
                        result: testResults[index],
                        index: index,
                      ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _SearchTableHeader extends StatelessWidget {
  const _SearchTableHeader();

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
          Expanded(flex: 3, child: _HeaderCell('Artefact')),
          Expanded(flex: 4, child: _HeaderCell('Test Case')),
          Expanded(flex: 3, child: _HeaderCell('Test Execution ID')),
          Expanded(flex: 2, child: _HeaderCell('Status')),
          Expanded(flex: 2, child: _HeaderCell('Track')),
          Expanded(flex: 3, child: _HeaderCell('Version')),
          Expanded(flex: 3, child: _HeaderCell('Environment')),
          Expanded(flex: 3, child: _HeaderCell('Test Plan')),
          Expanded(flex: 3, child: _HeaderCell('Actions')),
        ],
      ),
    );
  }
}

class _HeaderCell extends StatelessWidget {
  const _HeaderCell(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      alignment: Alignment.centerLeft,
      child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
    );
  }
}

class _SearchTableRow extends StatelessWidget {
  const _SearchTableRow({required this.result, required this.index});

  final SearchPageTableRow result;
  final int index;

  @override
  Widget build(BuildContext context) {
    final testResult = result.testResult;
    final execution = result.testExecution;
    final artefact = result.artefact;
    final buildInfo =
        '${result.artefactBuild.architecture}/${execution.environment.name}';
    return Container(
      constraints: const BoxConstraints(minHeight: 60),
      decoration: BoxDecoration(
        color: index.isEven ? Colors.white : Colors.grey[50],
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Expanded(flex: 3, child: _Cell(artefact.name)),
          Expanded(
            flex: 4,
            child: _TestCaseCell(
              name: testResult.name,
              category: testResult.category,
            ),
          ),
          Expanded(flex: 3, child: _Cell(execution.id.toString(), bold: true)),
          Expanded(flex: 2, child: _StatusCell(status: testResult.status)),
          Expanded(flex: 2, child: _Cell(artefact.track)),
          Expanded(flex: 3, child: _Cell(artefact.version)),
          Expanded(
            flex: 3,
            child: Tooltip(message: buildInfo, child: _Cell(buildInfo)),
          ),
          Expanded(
            flex: 3,
            child: Tooltip(
              message:
                  execution.testPlan.isNotEmpty
                      ? execution.testPlan
                      : 'Unknown',
              child: _Cell(
                execution.testPlan.isNotEmpty ? execution.testPlan : 'Unknown',
              ),
            ),
          ),
          Expanded(flex: 3, child: _ActionsCell(result: result)),
        ],
      ),
    );
  }
}

class _Cell extends StatelessWidget {
  const _Cell(this.value, {this.bold = false});

  final String value;
  final bool bold;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      alignment: Alignment.centerLeft,
      child: Text(
        value,
        style: TextStyle(
          fontSize: 14,
          fontWeight: bold ? FontWeight.w500 : FontWeight.normal,
        ),
        overflow: TextOverflow.ellipsis,
        maxLines: 1,
      ),
    );
  }
}

class _TestCaseCell extends StatelessWidget {
  const _TestCaseCell({required this.name, required this.category});

  final String name;
  final String category;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.center,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            name,
            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
            overflow: TextOverflow.ellipsis,
            maxLines: 2,
          ),
          if (category.isNotEmpty) ...[
            const SizedBox(height: 2),
            Text(
              category,
              style: TextStyle(fontSize: 12, color: Colors.grey[600]),
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
  const _StatusCell({required this.status});

  final TestResultStatus status;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          status.getIcon(),
          const SizedBox(width: 4),
          Expanded(
            child: Text(
              status.name.toUpperCase(),
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
              overflow: TextOverflow.ellipsis,
              maxLines: 1,
            ),
          ),
        ],
      ),
    );
  }
}

class _ActionsCell extends StatelessWidget {
  const _ActionsCell({required this.result});

  final SearchPageTableRow result;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(8),
      child: Wrap(
        spacing: 4,
        children: [
          InkWell(
            onTap:
                () => showDialog<void>(
                  context: context,
                  builder:
                      (_) => SearchPageTestResultDetailsDialog(result: result),
                ),
            child: _ActionLabel(icon: Icons.visibility, label: 'Details'),
          ),
          InkWell(
            onTap: () => _navigateToTestExecution(result),
            child: _ActionLabel(icon: Icons.launch, label: 'View Run'),
          ),
        ],
      ),
    );
  }

  void _navigateToTestExecution(SearchPageTableRow result) {
    launchUrl(
      Uri.base.replace(fragment: searchPageRunPath(result)),
      mode: LaunchMode.externalApplication,
    );
  }
}

class _ActionLabel extends StatelessWidget {
  const _ActionLabel({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: YaruColors.orange),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 12, color: YaruColors.orange)),
        ],
      ),
    );
  }
}
