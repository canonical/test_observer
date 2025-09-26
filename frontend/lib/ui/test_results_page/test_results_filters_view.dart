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

import '../../models/family_name.dart';
import '../../models/execution_metadata.dart';
import '../../models/test_results_filters.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../../providers/execution_metadata.dart';
import '../page_filters/multi_select_combobox.dart';
import '../page_filters/date_time_selector.dart';
import '../spacing.dart';

class TestResultsFiltersView extends ConsumerStatefulWidget {
  const TestResultsFiltersView({
    super.key,
    required this.initialFilters,
  });

  final TestResultsFilters initialFilters;

  @override
  ConsumerState<TestResultsFiltersView> createState() =>
      _TestResultsFiltersViewState();
}

class _TestResultsFiltersViewState
    extends ConsumerState<TestResultsFiltersView> {
  static const double _comboWidth = 260;
  static const double _controlHeight = 48;

  late TestResultsFilters _selectedFilters;

  @override
  void initState() {
    super.initState();
    _selectedFilters = widget.initialFilters;
  }

  @override
  void didUpdateWidget(covariant TestResultsFiltersView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialFilters != widget.initialFilters) {
      setState(() {
        _selectedFilters = widget.initialFilters;
      });
    }
  }

  Widget _box(Widget child) => SizedBox(width: _comboWidth, child: child);

  @override
  Widget build(BuildContext context) {
    final environments = ref.watch(allEnvironmentsProvider).value ?? [];
    final allFamilyOptions = FamilyName.values.map((f) => f.name).toList();
    final executionMetadata = ref.watch(executionMetadataProvider).value ??
        ExecutionMetadata(data: {});

    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.start,
      spacing: Spacing.level4,
      runSpacing: Spacing.level4,
      children: [
        _box(
          MultiSelectCombobox(
            title: 'Family',
            allOptions: allFamilyOptions,
            initialSelected: _selectedFilters.families.toSet(),
            onChanged: (val, isSelected) {
              setState(
                () => _selectedFilters = _selectedFilters.copyWith(
                  families: [
                    ..._selectedFilters.families.where((f) => f != val),
                    if (isSelected) val,
                  ],
                ),
              );
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Environment',
            allOptions: environments,
            initialSelected: _selectedFilters.environments.toSet(),
            onChanged: (val, isSelected) => setState(
              () => _selectedFilters = _selectedFilters.copyWith(
                environments: [
                  ..._selectedFilters.environments.where((e) => e != val),
                  if (isSelected) val,
                ],
              ),
            ),
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Test Case',
            allOptions: const [],
            initialSelected: _selectedFilters.testCases.toSet(),
            asyncSuggestionsCallback: (pattern) async {
              return await ref.read(suggestedTestCasesProvider(pattern).future);
            },
            minCharsForAsyncSearch: 2,
            onChanged: (val, isSelected) {
              setState(
                () => isSelected
                    ? _selectedFilters.testCases.add(val)
                    : _selectedFilters.testCases.remove(val),
              );
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Metadata',
            allOptions: executionMetadata.toStrings(),
            initialSelected:
                _selectedFilters.executionMetadata.toStrings().toSet(),
            onChanged: (val, isSelected) {
              final match = executionMetadata.findFromString(val);
              final newExecutionMetadata =
                  _selectedFilters.executionMetadata.toRows();
              if (isSelected) {
                newExecutionMetadata.add(match);
              } else {
                newExecutionMetadata.remove(match);
              }
              setState(
                () => _selectedFilters = _selectedFilters.copyWith(
                  executionMetadata: ExecutionMetadata.fromRows(
                    newExecutionMetadata,
                  ),
                ),
              );
            },
          ),
        ),
        _box(
          DateTimeSelector(
            title: 'From',
            initialDate: _selectedFilters.fromDate,
            onSelected: (date) {
              setState(
                () => _selectedFilters =
                    _selectedFilters.copyWith(fromDate: date),
              );
            },
          ),
        ),
        _box(
          DateTimeSelector(
            title: 'Until',
            initialDate: _selectedFilters.untilDate,
            onSelected: (date) {
              setState(
                () => _selectedFilters =
                    _selectedFilters.copyWith(untilDate: date),
              );
            },
          ),
        ),
        SizedBox(
          width: _comboWidth,
          height: _controlHeight,
          child: ElevatedButton(
            onPressed: () {
              context.go(_selectedFilters.toTestResultsUri().toString());
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
}
