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

import '../../providers/test_results.dart';
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

  final _familyKey = GlobalKey<MultiSelectComboboxState>();
  final _envKey = GlobalKey<MultiSelectComboboxState>();
  final _testKey = GlobalKey<MultiSelectComboboxState>();

  Widget _box(Widget child) => SizedBox(width: _comboWidth, child: child);

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
            onPressed: () {
              ref.read(testResultsSearchNotifierProvider.notifier).search();
            },
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
    final familySelections = ref.watch(familySelectionsProvider);

    final allOptions = familySelections.keys.toList()..sort();
    final selected = familySelections.entries
        .where((e) => e.value)
        .map((e) => e.key)
        .toSet();

    return MultiSelectCombobox(
      key: _familyKey,
      title: 'Family',
      allOptions: allOptions,
      initialSelected: selected,
      onChanged: (family, isSelected) {
        final current =
            Map<String, bool>.from(ref.read(familySelectionsProvider));
        current[family] = isSelected;
        ref.read(familySelectionsProvider.notifier).state = current;
      },
    );
  }

  Widget _buildEnvironmentSection() {
    final environmentsAsync = ref.watch(environmentsProvider);
    final selectedEnvironments = ref.watch(selectedEnvironmentsProvider);

    return environmentsAsync.when(
      data: (environments) => MultiSelectCombobox(
        key: _envKey,
        title: 'Environment',
        allOptions: environments,
        initialSelected: selectedEnvironments,
        onChanged: (environment, isSelected) {
          final current =
              Set<String>.from(ref.read(selectedEnvironmentsProvider));
          isSelected ? current.add(environment) : current.remove(environment);
          ref.read(selectedEnvironmentsProvider.notifier).state = current;
        },
      ),
      loading: () => MultiSelectCombobox(
        key: _envKey,
        title: 'Environment',
        allOptions: const [],
        initialSelected: const {},
        onChanged: (_, __) {},
      ),
      error: (error, _) => MultiSelectCombobox(
        key: _envKey,
        title: 'Environment (Error)',
        allOptions: const [],
        initialSelected: const {},
        onChanged: (_, __) {
          final ctx = _envKey.currentContext;
          if (ctx != null) {
            ScaffoldMessenger.of(ctx).showSnackBar(
              SnackBar(content: Text('Failed to load environments: $error')),
            );
          }
        },
      ),
    );
  }

  Widget _buildTestCaseSection() {
    final testCasesAsync = ref.watch(testCasesProvider);
    final selectedTestCases = ref.watch(selectedTestCasesProvider);

    return testCasesAsync.when(
      data: (testCases) => MultiSelectCombobox(
        key: _testKey,
        title: 'Test Case',
        allOptions: testCases,
        initialSelected: selectedTestCases,
        onChanged: (testCase, isSelected) {
          final current = Set<String>.from(ref.read(selectedTestCasesProvider));
          isSelected ? current.add(testCase) : current.remove(testCase);
          ref.read(selectedTestCasesProvider.notifier).state = current;
        },
      ),
      loading: () => MultiSelectCombobox(
        key: _testKey,
        title: 'Test Case',
        allOptions: const [],
        initialSelected: const {},
        onChanged: (_, __) {},
      ),
      error: (error, _) => MultiSelectCombobox(
        key: _testKey,
        title: 'Test Case (Error)',
        allOptions: const [],
        initialSelected: const {},
        onChanged: (_, __) {
          final ctx = _testKey.currentContext;
          if (ctx != null) {
            ScaffoldMessenger.of(ctx).showSnackBar(
              SnackBar(content: Text('Failed to load test cases: $error')),
            );
          }
        },
      ),
    );
  }
}
