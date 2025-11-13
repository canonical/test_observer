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
import '../../providers/execution_metadata.dart';
import '../../providers/issues.dart';
import '../../providers/test_results_artefacts.dart';
import '../../providers/test_results_environments.dart';
import '../../providers/test_results_test_cases.dart';
import '../issues.dart';
import '../page_filters/date_time_selector.dart';
import '../page_filters/multi_select_combobox.dart';
import '../spacing.dart';

enum FilterType {
  families,
  testResultStatuses,
  issues,
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
            Builder(
              builder: (context) {
                // Extract current state from IssuesFilter union
                String? selectedMetaOption;
                Set<int> selectedIssueIds = {};

                if (_selectedFilters.issues.isAny) {
                  selectedMetaOption = 'any';
                } else if (_selectedFilters.issues.isNone) {
                  selectedMetaOption = 'none';
                } else {
                  selectedIssueIds = _selectedFilters.issues.issuesList.toSet();
                }

                return MultiSelectCombobox<int>(
                  title: 'Issues',
                  metaOptions: const [
                    MetaOption(value: 'any', label: 'Has any issue'),
                    MetaOption(value: 'none', label: 'Has no issues'),
                  ],
                  selectedMetaOption: selectedMetaOption,
                  onMetaOptionChanged: (value) {
                    setState(() {
                      if (value == 'any') {
                        _selectedFilters = _selectedFilters.copyWith(
                          issues: const IssuesFilter.any(),
                        );
                      } else if (value == 'none') {
                        _selectedFilters = _selectedFilters.copyWith(
                          issues: const IssuesFilter.none(),
                        );
                      } else {
                        // Cleared - go back to list mode
                        _selectedFilters = _selectedFilters.copyWith(
                          issues: const IssuesFilter.list([]),
                        );
                      }
                      _notifyChanged(_selectedFilters);
                    });
                  },
                  asyncSuggestionsCallback: (pattern) async {
                    final issues = await ref.read(
                      issuesProvider(
                        q: pattern,
                        limit: 10,
                      ).future,
                    );
                    return issues.map((issue) => issue.id).toList();
                  },
                  itemBuilder: (issueId) {
                    // Use Consumer to load issue from cache
                    return Consumer(
                      builder: (context, ref, child) {
                        final issue = ref.watch(simpleIssueProvider(issueId));

                        // If not in cache, fetch it
                        if (issue == null) {
                          // Trigger fetch and show loading
                          ref
                              .read(simpleIssueProvider(issueId).notifier)
                              .fetchIfNeeded();
                          return const Padding(
                            padding: EdgeInsets.all(Spacing.level3),
                            child: Center(
                              child: YaruCircularProgressIndicator(
                                strokeWidth: 2,
                              ),
                            ),
                          );
                        }

                        return _buildIssueDisplay(issue);
                      },
                    );
                  },
                  initialSelected: selectedIssueIds,
                  onChanged: (issueId, isSelected) {
                    setState(() {
                      final currentIssueIds =
                          _selectedFilters.issues.issuesList;
                      final newIssueIds = Set<int>.from(currentIssueIds);

                      if (isSelected) {
                        newIssueIds.add(issueId);
                      } else {
                        newIssueIds.remove(issueId);
                      }

                      _selectedFilters = _selectedFilters.copyWith(
                        issues: IssuesFilter.list(newIssueIds.toList()),
                      );
                      _notifyChanged(_selectedFilters);
                    });
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
