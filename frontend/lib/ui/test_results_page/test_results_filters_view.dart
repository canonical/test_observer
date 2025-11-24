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

import '../../models/execution_metadata.dart';
import '../../models/family_name.dart';
import '../../models/issue.dart';
import '../../models/test_result.dart';
import '../../models/test_results_filters.dart';
import '../../models/user.dart';
import '../../providers/execution_metadata.dart';
import '../../providers/issues.dart';
import '../../providers/test_results_artefacts.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../../providers/users.dart';
import '../issues.dart';
import '../page_filters/date_time_selector.dart';
import '../page_filters/multi_select_combobox.dart';
import '../spacing.dart';

enum FilterType {
  families,
  testResultStatuses,
  issues,
  assignees,
  artefacts,
  environments,
  testCases,
  templateIds,
  metadata,
  dateRange,
}

class TestResultsFiltersView extends ConsumerStatefulWidget {
  const TestResultsFiltersView({
    super.key,
    required this.initialFilters,
    this.onApplyFilters,
    this.onChanged,
    this.enabledFilters,
  });

  final TestResultsFilters initialFilters;
  final Function(TestResultsFilters)? onApplyFilters;
  final Function(TestResultsFilters)? onChanged;
  final Set<FilterType>? enabledFilters;

  @override
  ConsumerState<TestResultsFiltersView> createState() =>
      _TestResultsFiltersViewState();
}

class _TestResultsFiltersViewState
    extends ConsumerState<TestResultsFiltersView> {
  static const double _comboWidth = 350;
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

  bool _isFilterEnabled(FilterType filter) {
    return widget.enabledFilters == null ||
        widget.enabledFilters!.contains(filter);
  }

  void _applyFilters() {
    if (widget.onApplyFilters != null) {
      // Use callback if provided
      widget.onApplyFilters!(_selectedFilters);
    } else {
      // Otherwise, navigate to test results page
      context.go(_selectedFilters.toTestResultsUri().toString());
    }
  }

  void _notifyChanged(TestResultsFilters filters) {
    if (widget.onChanged != null) {
      widget.onChanged!(filters);
    }
  }

  Widget _buildIssueDisplay(Issue issue) {
    return Padding(
      padding: const EdgeInsets.all(Spacing.level3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        spacing: Spacing.level2,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            spacing: Spacing.level3,
            children: [
              IssueSourceWidget(source: issue.source),
              IssueProjectWidget(project: issue.project),
              IssueLinkWidget(issue: issue),
            ],
          ),
          IssueTitleWidget(issue: issue),
        ],
      ),
    );
  }

  Widget _buildUserDisplay(User user) {
    final secondaryStyle = TextStyle(
      fontSize: 12,
      color: Theme.of(context).colorScheme.onSurfaceVariant,
    );

    return Padding(
      padding: const EdgeInsets.all(Spacing.level3),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        spacing: Spacing.level2,
        children: [
          Text(
            user.name,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          if (user.launchpadHandle != null)
            Text('@${user.launchpadHandle!}', style: secondaryStyle),
          Row(
            spacing: Spacing.level1,
            children: [
              Icon(
                Icons.email,
                size: 12,
                color: Theme.of(context).colorScheme.onSurfaceVariant,
              ),
              Text(user.email, style: secondaryStyle),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildIntListFilterCombobox<T>({
    required String title,
    required IntListFilter currentFilter,
    required List<MetaOption> metaOptions,
    required void Function(IntListFilter) onFilterChanged,
    required Future<List<int>> Function(String) asyncSuggestionsCallback,
    required Widget Function(int) itemBuilder,
  }) {
    String? selectedMetaOption;
    Set<int> selectedIds = {};

    if (currentFilter.isAny) {
      selectedMetaOption = 'any';
    } else if (currentFilter.isNone) {
      selectedMetaOption = 'none';
    } else {
      selectedIds = currentFilter.values.toSet();
    }

    return MultiSelectCombobox<int>(
      title: title,
      metaOptions: metaOptions,
      selectedMetaOption: selectedMetaOption,
      onMetaOptionChanged: (value) {
        setState(() {
          if (value == 'any') {
            onFilterChanged(const IntListFilter.any());
          } else if (value == 'none') {
            onFilterChanged(const IntListFilter.none());
          } else {
            onFilterChanged(const IntListFilter.list([]));
          }
        });
      },
      asyncSuggestionsCallback: asyncSuggestionsCallback,
      itemBuilder: itemBuilder,
      initialSelected: selectedIds,
      onChanged: (id, isSelected) {
        setState(() {
          final currentIds = currentFilter.values;
          final newIds = Set<int>.from(currentIds);

          if (isSelected) {
            newIds.add(id);
          } else {
            newIds.remove(id);
          }

          onFilterChanged(IntListFilter.list(newIds.toList()));
        });
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final allFamilyOptions = FamilyName.values.map((f) => f.name).toList();
    final allTestResultStatusesOptions =
        TestResultStatus.values.map((s) => s.name).toList();
    final executionMetadata = ref.watch(executionMetadataProvider).value ??
        ExecutionMetadata(data: {});

    return Wrap(
      crossAxisAlignment: WrapCrossAlignment.start,
      spacing: Spacing.level4,
      runSpacing: Spacing.level4,
      children: [
        if (_isFilterEnabled(FilterType.families))
          _box(
            MultiSelectCombobox<String>(
              title: 'Family',
              allOptions: allFamilyOptions,
              showAllOptionsWithoutSearch: true,
              itemToString: (family) => family,
              initialSelected: _selectedFilters.families.toSet(),
              onChanged: (val, isSelected) {
                setState(() {
                  _selectedFilters = _selectedFilters.copyWith(
                    families: [
                      ..._selectedFilters.families.where((f) => f != val),
                      if (isSelected) val,
                    ],
                  );
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.testResultStatuses))
          _box(
            MultiSelectCombobox<String>(
              title: 'Status',
              allOptions: allTestResultStatusesOptions,
              itemToString: (status) => status,
              initialSelected: _selectedFilters.testResultStatuses
                  .map((s) => s.name)
                  .toSet(),
              onChanged: (val, isSelected) {
                setState(() {
                  final status = TestResultStatus.fromString(val);
                  _selectedFilters = _selectedFilters.copyWith(
                    testResultStatuses: [
                      ..._selectedFilters.testResultStatuses
                          .where((s) => s != status),
                      if (isSelected) status,
                    ],
                  );
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.issues))
          _box(
            _buildIntListFilterCombobox(
              title: 'Issues',
              currentFilter: _selectedFilters.issues,
              metaOptions: const [
                MetaOption(value: 'any', label: 'Has any issue'),
                MetaOption(value: 'none', label: 'Has no issues'),
              ],
              onFilterChanged: (filter) {
                _selectedFilters = _selectedFilters.copyWith(issues: filter);
                _notifyChanged(_selectedFilters);
              },
              asyncSuggestionsCallback: (pattern) async {
                final issues = await ref.read(
                  issuesProvider(q: pattern, limit: 10).future,
                );
                return issues.map((issue) => issue.id).toList();
              },
              itemBuilder: (issueId) {
                return Consumer(
                  builder: (context, ref, child) {
                    final issue = ref.watch(simpleIssueProvider(issueId));

                    if (issue == null) {
                      ref
                          .read(simpleIssueProvider(issueId).notifier)
                          .fetchIfNeeded();
                      return const Padding(
                        padding: EdgeInsets.all(Spacing.level3),
                        child: Center(
                          child: YaruCircularProgressIndicator(strokeWidth: 2),
                        ),
                      );
                    }

                    return _buildIssueDisplay(issue);
                  },
                );
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.assignees))
          _box(
            _buildIntListFilterCombobox(
              title: 'Assignees',
              currentFilter: _selectedFilters.assignees,
              metaOptions: const [
                MetaOption(value: 'any', label: 'Has any assignee'),
                MetaOption(value: 'none', label: 'Has no assignee'),
              ],
              onFilterChanged: (filter) {
                _selectedFilters = _selectedFilters.copyWith(assignees: filter);
                _notifyChanged(_selectedFilters);
              },
              asyncSuggestionsCallback: (pattern) async {
                final users = await ref.read(
                  usersProvider(q: pattern, limit: 10).future,
                );
                return users.map((user) => user.id).toList();
              },
              itemBuilder: (userId) {
                return Consumer(
                  builder: (context, ref, child) {
                    final user = ref.watch(simpleUserProvider(userId));

                    if (user == null) {
                      ref
                          .read(simpleUserProvider(userId).notifier)
                          .fetchIfNeeded();
                      return const Padding(
                        padding: EdgeInsets.all(Spacing.level3),
                        child: Center(
                          child: YaruCircularProgressIndicator(strokeWidth: 2),
                        ),
                      );
                    }

                    return _buildUserDisplay(user);
                  },
                );
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.artefacts))
          _box(
            MultiSelectCombobox<String>(
              title: 'Artefact',
              initialSelected: _selectedFilters.artefacts.toSet(),
              asyncSuggestionsCallback: (pattern) async {
                return await ref.read(
                  suggestedArtefactsProvider(
                    pattern,
                    _selectedFilters.families,
                  ).future,
                );
              },
              minCharsForAsyncSearch: 2,
              onChanged: (val, isSelected) {
                setState(() {
                  _selectedFilters = _selectedFilters.copyWith(
                    artefacts: [
                      ..._selectedFilters.artefacts.where((a) => a != val),
                      if (isSelected) val,
                    ],
                  );
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.environments))
          _box(
            MultiSelectCombobox<String>(
              title: 'Environment',
              initialSelected: _selectedFilters.environments.toSet(),
              asyncSuggestionsCallback: (pattern) async {
                return await ref.read(
                  suggestedEnvironmentsProvider(
                    pattern,
                    _selectedFilters.families,
                  ).future,
                );
              },
              minCharsForAsyncSearch: 2,
              onChanged: (val, isSelected) {
                setState(() {
                  _selectedFilters = _selectedFilters.copyWith(
                    environments: [
                      ..._selectedFilters.environments.where((e) => e != val),
                      if (isSelected) val,
                    ],
                  );
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.testCases))
          _box(
            MultiSelectCombobox<String>(
              title: 'Test Case',
              initialSelected: _selectedFilters.testCases.toSet(),
              asyncSuggestionsCallback: (pattern) async {
                return await ref.read(
                  suggestedTestCasesProvider(pattern, _selectedFilters.families)
                      .future,
                );
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
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.metadata))
          _box(
            MultiSelectCombobox<String>(
              title: 'Metadata',
              allOptions: executionMetadata.toStrings(),
              itemToString: (metadata) => metadata,
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
                setState(() {
                  _selectedFilters = _selectedFilters.copyWith(
                    executionMetadata: ExecutionMetadata.fromRows(
                      newExecutionMetadata,
                    ),
                  );
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        if (_isFilterEnabled(FilterType.dateRange)) ...[
          _box(
            DateTimeSelector(
              title: 'From',
              initialDate: _selectedFilters.fromDate,
              onSelected: (date) {
                setState(() {
                  _selectedFilters = _selectedFilters.copyWith(fromDate: date);
                  _notifyChanged(_selectedFilters);
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
                  _notifyChanged(_selectedFilters);
                });
              },
            ),
          ),
        ],
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
}
