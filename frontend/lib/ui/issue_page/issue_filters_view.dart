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

import '../../models/test_results_filters.dart';
import '../../models/family_name.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../page_filters/multi_select_combobox.dart';
import '../page_filters/date_time_selector.dart';
import '../spacing.dart';

class IssueFiltersView extends ConsumerStatefulWidget {
  const IssueFiltersView({
    super.key,
    required this.currentFilters,
    required this.onFiltersChanged,
  });

  final TestResultsFilters currentFilters;
  final Function(TestResultsFilters) onFiltersChanged;

  @override
  ConsumerState<IssueFiltersView> createState() => _IssueFiltersViewState();
}

class _IssueFiltersViewState extends ConsumerState<IssueFiltersView> {
  static const double _comboWidth = 260;
  static const double _controlHeight = 48;

  late TestResultsFilters _selectedFilters;

  @override
  void initState() {
    super.initState();
    _selectedFilters = widget.currentFilters;
  }

  @override
  void didUpdateWidget(covariant IssueFiltersView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.currentFilters != widget.currentFilters) {
      setState(() {
        _selectedFilters = widget.currentFilters;
      });
    }
  }

  Widget _box(Widget child) => SizedBox(width: _comboWidth, child: child);

  @override
  Widget build(BuildContext context) {
    final environments = ref.watch(allEnvironmentsProvider).value ?? [];
    final allFamilyOptions = FamilyName.values.map((f) => f.name).toList();

    return Wrap(
      spacing: Spacing.level4,
      runSpacing: Spacing.level3,
      children: [
        _box(
          MultiSelectCombobox(
            title: 'Families',
            allOptions: allFamilyOptions,
            initialSelected: _selectedFilters.families.toSet(),
            onChanged: (val, isSelected) {
              setState(() {
                _selectedFilters = _selectedFilters.copyWith(
                  families: isSelected
                      ? (_selectedFilters.families + [val])
                      : _selectedFilters.families
                          .where((f) => f != val)
                          .toList(),
                );
              });
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Environments',
            allOptions: environments,
            initialSelected: _selectedFilters.environments.toSet(),
            onChanged: (val, isSelected) {
              setState(() {
                _selectedFilters = _selectedFilters.copyWith(
                  environments: isSelected
                      ? (_selectedFilters.environments + [val])
                      : _selectedFilters.environments
                          .where((e) => e != val)
                          .toList(),
                );
              });
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Test Cases',
            allOptions: const [],
            initialSelected: _selectedFilters.testCases.toSet(),
            asyncSuggestionsCallback: (pattern) async {
              return await ref.read(suggestedTestCasesProvider(pattern).future);
            },
            minCharsForAsyncSearch: 2,
            onChanged: (val, isSelected) {
              setState(() {
                _selectedFilters = _selectedFilters.copyWith(
                  testCases: isSelected
                      ? (_selectedFilters.testCases + [val])
                      : _selectedFilters.testCases
                          .where((tc) => tc != val)
                          .toList(),
                );
              });
            },
          ),
        ),
        _box(
          DateTimeSelector(
            title: 'From',
            initialDate: _selectedFilters.fromDate,
            onSelected: (date) {
              setState(() {
                _selectedFilters = _selectedFilters.copyWith(fromDate: date);
              });
            },
          ),
        ),
        _box(
          DateTimeSelector(
            title: 'Until',
            initialDate: _selectedFilters.untilDate,
            onSelected: (date) {
              setState(() {
                _selectedFilters = _selectedFilters.copyWith(untilDate: date);
              });
            },
          ),
        ),
        SizedBox(
          width: _comboWidth,
          height: _controlHeight,
          child: ElevatedButton(
            onPressed: () {
              widget.onFiltersChanged(_selectedFilters);
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
