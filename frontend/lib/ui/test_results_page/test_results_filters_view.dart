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

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import '../../models/family_name.dart';
import '../../models/execution_metadata.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../../providers/execution_metadata.dart';
import '../page_filters/multi_select_combobox.dart';
import '../spacing.dart';

class TestResultsFiltersView extends ConsumerStatefulWidget {
  const TestResultsFiltersView({
    super.key,
    required this.pageUri,
  });

  final Uri pageUri;

  @override
  ConsumerState<TestResultsFiltersView> createState() =>
      _TestResultsFiltersViewState();
}

class _TestResultsFiltersViewState
    extends ConsumerState<TestResultsFiltersView> {
  static const double _comboWidth = 260;
  static const double _controlHeight = 48;

  late Set<String> _families;
  late Set<String> _envs;
  late Set<String> _tests;
  late Set<(String, String)> _executionMetadata;

  @override
  void initState() {
    super.initState();
    _loadFromUri();
  }

  @override
  void didUpdateWidget(covariant TestResultsFiltersView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.pageUri.toString() != widget.pageUri.toString()) {
      _loadFromUri();
      setState(() {});
    }
  }

  void _loadFromUri() {
    Set<String> readParam(String key) {
      final params = widget.pageUri.queryParametersAll;
      final raw = params[key] ?? const <String>[];
      return raw.expand((s) => s.split(',')).where((s) => s.isNotEmpty).toSet();
    }

    _families = readParam('families');
    _envs = readParam('environments');
    _tests = readParam('test_cases');
    _executionMetadata = ExecutionMetadata.fromQueryParams(
      widget.pageUri.queryParametersAll['execution_metadata'] ?? [],
    ).toRows();
  }

  Map<String, String> _toQueryParams() {
    final qp = <String, String>{};
    if (_families.isNotEmpty) {
      qp['families'] = _families.map((f) => f.toLowerCase()).join(',');
    }
    if (_envs.isNotEmpty) {
      qp['environments'] = _envs.join(',');
    }
    if (_tests.isNotEmpty) {
      qp['test_cases'] = _tests.join(',');
    }
    if (_executionMetadata.isNotEmpty) {
      qp['execution_metadata'] = ExecutionMetadata.fromRows(_executionMetadata)
          .toQueryParams()
          .join(',');
    }
    return qp;
  }

  Widget _box(Widget child) => SizedBox(width: _comboWidth, child: child);

  @override
  Widget build(BuildContext context) {
    final environments = ref.watch(allEnvironmentsProvider).value ?? [];
    final testCases = ref.watch(allTestCasesProvider).value ?? [];
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
            initialSelected: _families,
            onChanged: (val, isSelected) {
              setState(
                () => isSelected ? _families.add(val) : _families.remove(val),
              );
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Environment',
            allOptions: environments,
            initialSelected: _envs,
            onChanged: (val, isSelected) {
              setState(() => isSelected ? _envs.add(val) : _envs.remove(val));
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Test Case',
            allOptions: testCases,
            initialSelected: _tests,
            onChanged: (val, isSelected) {
              setState(() => isSelected ? _tests.add(val) : _tests.remove(val));
            },
          ),
        ),
        _box(
          MultiSelectCombobox(
            title: 'Metadata',
            allOptions: executionMetadata
                .toRows()
                .map((pair) => '${pair.$1} ${pair.$2}')
                .toList(),
            initialSelected: _executionMetadata
                .map((pair) => '${pair.$1} ${pair.$2}')
                .toSet(),
            onChanged: (val, isSelected) {
              final match = executionMetadata.toRows().firstWhere(
                    (pair) => '${pair.$1} ${pair.$2}' == val,
                  );
              setState(
                () => isSelected
                    ? _executionMetadata.add(match)
                    : _executionMetadata.remove(match),
              );
            },
          ),
        ),
        SizedBox(
          width: _comboWidth,
          height: _controlHeight,
          child: ElevatedButton(
            onPressed: () {
              final newUri =
                  widget.pageUri.replace(queryParameters: _toQueryParams());
              context.go(newUri.toString());
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
