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
    final current = Set<String>.from(state.familySelections);
    if (isSelected) {
      current.add(family);
    } else {
      current.remove(family);
    }
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

    if (state.familySelections.isNotEmpty) {
      params['families'] =
          state.familySelections.map((f) => f.toLowerCase()).join(',');
    }

    if (state.selectedEnvironments.isNotEmpty) {
      params['environments'] = state.selectedEnvironments.join(',');
    }

    if (state.selectedTestCases.isNotEmpty) {
      params['test_cases'] = state.selectedTestCases.join(',');
    }

    return params;
  }

  void loadFromQueryParams(Map<String, List<String>> queryParamsAll) {
    final familiesValues = queryParamsAll['families'] ?? [];
    final familySelections = familiesValues.isNotEmpty
        ? familiesValues.first.split(',').toSet()
        : <String>{};

    final environmentsValues = queryParamsAll['environments'] ?? [];
    final selectedEnvironments = environmentsValues.isNotEmpty
        ? environmentsValues.first.split(',').toSet()
        : <String>{};

    final testCasesValues = queryParamsAll['test_cases'] ?? [];
    final selectedTestCases = testCasesValues.isNotEmpty
        ? testCasesValues.first.split(',').toSet()
        : <String>{};

    state = TestResultsFiltersState(
      familySelections: familySelections,
      selectedEnvironments: selectedEnvironments,
      selectedTestCases: selectedTestCases,
    );
  }
}

class TestResultsFiltersState {
  final Set<String> familySelections;
  final Set<String> selectedEnvironments;
  final Set<String> selectedTestCases;

  const TestResultsFiltersState({
    this.familySelections = const {},
    this.selectedEnvironments = const {},
    this.selectedTestCases = const {},
  });

  TestResultsFiltersState copyWith({
    Set<String>? familySelections,
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
