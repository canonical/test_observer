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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../models/issue.dart';
import '../../models/test_results_filters.dart';
import '../../providers/issue_test_results.dart';
import '../spacing.dart';
import '../test_results_page/test_results_table.dart';
import '../test_results_page/test_results_filters_view.dart';
import '../test_results_page/bulk_operations/bulk_operation_buttons.dart';

class TestResultsSection extends ConsumerStatefulWidget {
  const TestResultsSection({super.key, required this.issue});

  final Issue issue;

  @override
  ConsumerState<TestResultsSection> createState() => _TestResultsSectionState();
}

class _TestResultsSectionState extends ConsumerState<TestResultsSection> {
  bool showFilters = false;
  late TestResultsFilters _currentFilters;

  @override
  void initState() {
    super.initState();
    // Initialize with filters that include this issue ID
    _currentFilters = TestResultsFilters(
      issues: IntListFilter.list([widget.issue.id]),
    );
  }

  void _updateFilters(TestResultsFilters newFilters) {
    setState(() {
      // Always ensure the issue ID is included in the filters
      _currentFilters = newFilters.copyWith(
        issues: IntListFilter.list([widget.issue.id]),
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final testResultsAsync = ref.watch(
      issueTestResultsProvider(
        widget.issue.id,
        _currentFilters,
      ),
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      spacing: Spacing.level4,
      children: [
        // Test Results section with filter toggle
        Row(
          children: [
            Text(
              'Test Results',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
            const Spacer(),
            YaruOptionButton(
              child: const Icon(Icons.filter_alt),
              onPressed: () {
                setState(() {
                  showFilters = !showFilters;
                });
              },
            ),
          ],
        ),

        if (showFilters) ...[
          TestResultsFiltersView(
            initialFilters: _currentFilters,
            onApplyFilters: _updateFilters,
            enabledFilters: const {
              FilterType.families,
              FilterType.artefacts,
              FilterType.environments,
              FilterType.testCases,
              FilterType.dateRange,
            },
          ),
        ],

        BulkOperationsButtons(
          filters: _currentFilters,
          enabledOperations: const {
            BulkOperationType.createRerunRequests,
            BulkOperationType.deleteRerunRequests,
          },
        ),

        testResultsAsync.when(
          data: (testResultsData) {
            return Padding(
              padding: const EdgeInsets.only(bottom: Spacing.level3),
              child: Text(
                'Found ${testResultsData.count} results (showing ${testResultsData.testResults.length})',
                style: Theme.of(context).textTheme.bodyLarge,
              ),
            );
          },
          loading: () => const SizedBox.shrink(),
          error: (error, stack) => const SizedBox.shrink(),
        ),

        testResultsAsync.when(
          data: (testResultsData) {
            if (testResultsData.testResults.isEmpty) {
              return const Center(
                child: Text('No test results found for this issue.'),
              );
            }

            return TestResultsTable(
              testResults: testResultsData.testResults,
            );
          },
          loading: () => const Center(
            child: YaruCircularProgressIndicator(),
          ),
          error: (error, stack) => Center(
            child: Text('Error loading test results: $error'),
          ),
        ),
      ],
    );
  }
}
