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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:freezed_annotation/freezed_annotation.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

part 'test_results_filters.freezed.dart';
part 'test_results_filters.g.dart';

@riverpod
TestResultsFiltersState testResultsFiltersFromUri(Ref ref, Uri pageUri) {
  final parameters = pageUri.queryParametersAll;

  final familiesValues = parameters['families'] ?? [];
  final selectedFamilies = familiesValues.isNotEmpty
      ? familiesValues.first.split(',').toSet()
      : <String>{};

  final environmentsValues = parameters['environments'] ?? [];
  final selectedEnvironments = environmentsValues.isNotEmpty
      ? environmentsValues.first.split(',').toSet()
      : <String>{};

  final testCasesValues = parameters['test_cases'] ?? [];
  final selectedTestCases = testCasesValues.isNotEmpty
      ? testCasesValues.first.split(',').toSet()
      : <String>{};

  return TestResultsFiltersState(
    selectedFamilies: selectedFamilies,
    selectedEnvironments: selectedEnvironments,
    selectedTestCases: selectedTestCases,
  );
}

@riverpod
class TestResultsFilters extends _$TestResultsFilters {
  @override
  TestResultsFiltersState build() {
    return const TestResultsFiltersState();
  }

  void updateFamilySelection(String family, bool isSelected) {
    final current = {...state.selectedFamilies};
    if (isSelected) {
      current.add(family);
    } else {
      current.remove(family);
    }
    state = state.copyWith(selectedFamilies: current);
  }

  void updateEnvironmentSelection(String environment, bool isSelected) {
    final current = {...state.selectedEnvironments};
    if (isSelected) {
      current.add(environment);
    } else {
      current.remove(environment);
    }
    state = state.copyWith(selectedEnvironments: current);
  }

  void updateTestCaseSelection(String testCase, bool isSelected) {
    final current = {...state.selectedTestCases};
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

    if (state.selectedFamilies.isNotEmpty) {
      params['families'] =
          state.selectedFamilies.map((f) => f.toLowerCase()).join(',');
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
    final selectedFamilies = familiesValues.isNotEmpty
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
      selectedFamilies: selectedFamilies,
      selectedEnvironments: selectedEnvironments,
      selectedTestCases: selectedTestCases,
    );
  }
}

@freezed
abstract class TestResultsFiltersState with _$TestResultsFiltersState {
  const factory TestResultsFiltersState({
    @Default(<String>{}) Set<String> selectedFamilies,
    @Default(<String>{}) Set<String> selectedEnvironments,
    @Default(<String>{}) Set<String> selectedTestCases,
  }) = _TestResultsFiltersState;

  factory TestResultsFiltersState.fromJson(Map<String, dynamic> json) =>
      _$TestResultsFiltersStateFromJson(json);
}
