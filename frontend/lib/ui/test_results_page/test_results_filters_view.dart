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
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../providers/test_results_filters.dart';
import '../../providers/test_results_search.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../../routing.dart';
import '../page_filters/multi_select_combobox.dart';
import '../spacing.dart';

class TestResultsFiltersView extends ConsumerStatefulWidget {
  const TestResultsFiltersView({super.key});

  @override
  ConsumerState<TestResultsFiltersView> createState() =>
      _TestResultsFiltersViewState();
}

class _TestResultsFiltersViewState
    extends ConsumerState<TestResultsFiltersView> {
  static const double _comboWidth = 260;
  static const double _controlHeight = 48;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final uri = AppRoutes.uriFromContext(context);
      ref
          .read(testResultsFiltersProvider.notifier)
          .loadFromQueryParams(uri.queryParametersAll);
    });
  }

  Widget _box(Widget child) => SizedBox(width: _comboWidth, child: child);

  void _applyFilters() {
    // Update URL with current filter state
    final queryParams =
        ref.read(testResultsFiltersProvider.notifier).toQueryParams();
    final uri = AppRoutes.uriFromContext(context);
    context.go(uri.replace(queryParameters: queryParams).toString());

    // Trigger search
    ref.read(testResultsSearchProvider.notifier).search();
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _box(_buildFamilySection()),
        const SizedBox(width: Spacing.level4),
        _box(_buildEnvironmentSection()),
        const SizedBox(width: Spacing.level4),
        _box(_buildTestCaseSection()),
        const SizedBox(width: Spacing.level4),
        SizedBox(
          width: _comboWidth,
          height: _controlHeight,
          child: ElevatedButton(
            onPressed: _applyFilters,
            style: ElevatedButton.styleFrom(
              backgroundColor: YaruColors.orange,
              foregroundColor: Colors.white,
              minimumSize: const Size.fromHeight(_controlHeight),
              padding: EdgeInsets.zero,
            ),
            child: const Text('Apply Filters'),
          ),
        ),
      ],
    );
  }

  Widget _buildFamilySection() {
    final filters = ref.watch(testResultsFiltersProvider);

    const allFamilyOptions = ['snap', 'deb', 'charm', 'image'];

    return MultiSelectCombobox(
      key: const ValueKey(
        'family-filter',
      ),
      title: 'Family',
      allOptions: allFamilyOptions,
      initialSelected: filters.selectedFamilies,
      onChanged: (family, isSelected) {
        ref
            .read(testResultsFiltersProvider.notifier)
            .updateFamilySelection(family, isSelected);
      },
    );
  }

  Widget _buildEnvironmentSection() {
    final filters = ref.watch(testResultsFiltersProvider);
    final environments = ref.watch(allEnvironmentsProvider).value ?? [];

    return MultiSelectCombobox(
      key: const ValueKey(
        'environment-filter',
      ),
      title: 'Environment',
      allOptions: environments,
      initialSelected: filters.selectedEnvironments,
      onChanged: (environment, isSelected) {
        ref
            .read(testResultsFiltersProvider.notifier)
            .updateEnvironmentSelection(environment, isSelected);
      },
    );
  }

  Widget _buildTestCaseSection() {
    final filters = ref.watch(testResultsFiltersProvider);
    final testCases = ref.watch(allTestCasesProvider).value ?? [];

    return MultiSelectCombobox(
      key: const ValueKey(
        'testcase-filter',
      ),
      title: 'Test Case',
      allOptions: testCases,
      initialSelected: filters.selectedTestCases,
      onChanged: (testCase, isSelected) {
        ref
            .read(testResultsFiltersProvider.notifier)
            .updateTestCaseSelection(testCase, isSelected);
      },
    );
  }
}
