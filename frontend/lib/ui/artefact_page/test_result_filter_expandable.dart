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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import '../../../models/test_result.dart';
import '../../../providers/test_results.dart';
import '../../../ui/test_results_page/test_results_helpers.dart';
import '../expandable.dart';
import 'test_result_expandable.dart';

class TestResultsFilterExpandable extends ConsumerStatefulWidget {
  const TestResultsFilterExpandable({
    super.key,
    required this.statusToFilterBy,
    required this.testExecutionId,
    required this.artefactId,
    this.testResultIdToExpand,
  });

  final TestResultStatus statusToFilterBy;
  final int testExecutionId;
  final int artefactId;
  final int? testResultIdToExpand;

  @override
  ConsumerState<TestResultsFilterExpandable> createState() =>
      _TestResultsFilterExpandableState();
}

class _TestResultsFilterExpandableState
    extends ConsumerState<TestResultsFilterExpandable> {
  int _limit = 20;

  @override
  Widget build(BuildContext context) {
    final testResultsAsync = ref.watch(testResultsProvider(widget.testExecutionId));

    return testResultsAsync.when(
      loading: () => const CircularProgressIndicator(),
      error: (error, stackTrace) => Text('Error: $error'),
      data: (testResults) {
        final filteredResults = testResults
            .where((result) => result.status == widget.statusToFilterBy)
            .toList();

        final shouldExpandStatus = widget.testResultIdToExpand != null &&
            filteredResults.any((result) => result.id == widget.testResultIdToExpand);

        if (shouldExpandStatus && widget.testResultIdToExpand != null) {
          final targetIndex = filteredResults
              .indexWhere((r) => r.id == widget.testResultIdToExpand);
          if (targetIndex != -1 && targetIndex >= _limit) {
            _limit = targetIndex + 10;
          }
        }

        final visibleResults = filteredResults.take(_limit).toList();

        return RepaintBoundary(
          child: Expandable(
            initiallyExpanded: shouldExpandStatus,
            title: Row(
              children: [
                TestResultHelpers.getStatusIcon(widget.statusToFilterBy),
                const SizedBox(width: 8),
                Text(widget.statusToFilterBy.name),
                Text(' ${filteredResults.length}'),
              ],
            ),
            children: [
              ...visibleResults.map(
                (result) => TestResultExpandable(
                  testExecutionId: widget.testExecutionId,
                  testResult: result,
                  artefactId: widget.artefactId,
                  testResultIdToExpand: widget.testResultIdToExpand,
                ),
              ),
              if (filteredResults.length > _limit)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8.0),
                  child: TextButton(
                    onPressed: () {
                      setState(() {
                        _limit += 20;
                      });
                    },
                    child: Text('Load more (${filteredResults.length - _limit} remaining)'),
                  ),
                ),
            ],
          ),
        );
      },
    );
  }
}

