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

import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'test_results_filters.g.dart';

@riverpod
class TestResultsFilters extends _$TestResultsFilters {
  @override
  TestResultsFiltersState build() {
    return const TestResultsFiltersState();
  }

  void updateFamilySelection(String family, bool isSelected) {
    final current = Map<String, bool>.from(state.familySelections);
    current[family] = isSelected;
    state = state.copyWith(familySelections: current);
  }

  void updateEnvironmentSelection(String environment, bool isSelected) {
    final current = Set<String>.from(state.selectedEnvironments);
    if (isSelected) {
      current.add(environment);
    } else {
      current.remove(environment);
    }
    state = state.copyWith(selectedEnvironments: current);
  }

  void updateTestCaseSelection(String testCase, bool isSelected) {
    final current = Set<String>.from(state.selectedTestCases);
    if (isSelected) {
      current.add(testCase);
    } else {
      current.remove(testCase);
    }
    state = state.copyWith(selectedTestCases: current);
  }

  void clearAllFilters() {
    state = const TestResultsFiltersState();
  }

  Map<String, String> toQueryParams() {
    final params = <String, String>{};

    final selectedFamilies = state.familySelections.entries
        .where((entry) => entry.value)
        .map((entry) => entry.key.toLowerCase())
        .toList();
    if (selectedFamilies.isNotEmpty) {
      params['families'] = selectedFamilies.join(',');
    }

    if (state.selectedEnvironments.isNotEmpty) {
      params['environments'] = state.selectedEnvironments.join(',');
    }

    if (state.selectedTestCases.isNotEmpty) {
      params['test_cases'] = state.selectedTestCases.join(',');
    }

    return params;
  }

  void loadFromQueryParams(Map<String, String> queryParams) {
    final familySelections = <String, bool>{
      'snap': false,
      'deb': false,
      'charm': false,
      'image': false,
    };

    final familiesParam = queryParams['families'];
    if (familiesParam != null) {
      final families = familiesParam.split(',');
      for (final family in families) {
        if (familySelections.containsKey(family)) {
          familySelections[family] = true;
        }
      }
    }

    final environmentsParam = queryParams['environments'];
    final selectedEnvironments =
        environmentsParam?.split(',').toSet() ?? <String>{};

    final testCasesParam = queryParams['test_cases'];
    final selectedTestCases = testCasesParam?.split(',').toSet() ?? <String>{};

    state = TestResultsFiltersState(
      familySelections: familySelections,
      selectedEnvironments: selectedEnvironments,
      selectedTestCases: selectedTestCases,
    );
  }
}

class TestResultsFiltersState {
  final Map<String, bool> familySelections;
  final Set<String> selectedEnvironments;
  final Set<String> selectedTestCases;

  const TestResultsFiltersState({
    this.familySelections = const {
      'snap': false,
      'deb': false,
      'charm': false,
      'image': false,
    },
    this.selectedEnvironments = const {},
    this.selectedTestCases = const {},
  });

  TestResultsFiltersState copyWith({
    Map<String, bool>? familySelections,
    Set<String>? selectedEnvironments,
    Set<String>? selectedTestCases,
  }) {
    return TestResultsFiltersState(
      familySelections: familySelections ?? this.familySelections,
      selectedEnvironments: selectedEnvironments ?? this.selectedEnvironments,
      selectedTestCases: selectedTestCases ?? this.selectedTestCases,
    );
  }
}
