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

import '../models/attachment_rule_filters.dart';
import '../models/execution_metadata.dart';

class AttachmentRuleFiltersWidget extends StatelessWidget {
  final AttachmentRuleFilters filters;
  final bool editable;
  final AttachmentRuleFilters initialSelectedFilters;
  final void Function(AttachmentRuleFilters selectedFilters)? onChanged;

  const AttachmentRuleFiltersWidget({
    super.key,
    required this.filters,
    this.editable = true,
    this.initialSelectedFilters = const AttachmentRuleFilters(),
    this.onChanged,
  });

  String? _validate(AttachmentRuleFilters? filters) {
    if (editable && (filters == null || !filters.hasMoreThanStatusFilter)) {
      return 'Select at least one filter.';
    }
    return null;
  }

  Widget _buildFilterSection<T>({
    required BuildContext context,
    required String label,
    required List<T> allValues,
    Map<T, String> displayValues = const {},
    Set<T> selectedValues = const {},
    required void Function(Set<T> newSelected) onChanged,
  }) {
    if (allValues.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: Theme.of(context).textTheme.titleMedium),
        if (editable)
          ...allValues.map(
            (v) => CheckboxListTile(
              title: Text(displayValues[v] ?? v.toString()),
              value: selectedValues.contains(v),
              onChanged: (checked) {
                final newSelected = Set<T>.from(selectedValues);
                if (checked == true) {
                  newSelected.add(v);
                } else {
                  newSelected.remove(v);
                }
                onChanged(newSelected);
              },
            ),
          )
        else
          ...allValues.map(
            (v) => ListTile(
              title: Text(displayValues[v] ?? v.toString()),
            ),
          ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return FormField<AttachmentRuleFilters>(
      initialValue: initialSelectedFilters,
      validator: _validate,
      builder: (field) {
        final selected = field.value ?? const AttachmentRuleFilters();
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (field.hasError)
              Text(
                field.errorText!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            if (filters.hasFilters) ...[
              _buildFilterSection(
                context: context,
                label: 'Families',
                allValues: filters.families,
                selectedValues: selected.families.toSet(),
                onChanged: (newFamilies) {
                  final newFilters =
                      selected.copyWith(families: newFamilies.toList());
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
              _buildFilterSection(
                context: context,
                label: 'Environments',
                allValues: filters.environmentNames,
                selectedValues: selected.environmentNames.toSet(),
                onChanged: (newEnvironments) {
                  final newFilters = selected.copyWith(
                    environmentNames: newEnvironments.toList(),
                  );
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
              _buildFilterSection(
                context: context,
                label: 'Test Cases',
                allValues: filters.testCaseNames,
                selectedValues: selected.testCaseNames.toSet(),
                onChanged: (newTestCases) {
                  final newFilters =
                      selected.copyWith(testCaseNames: newTestCases.toList());
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
              _buildFilterSection(
                context: context,
                label: 'Template IDs',
                allValues: filters.templateIds,
                selectedValues: selected.templateIds.toSet(),
                onChanged: (newTemplateIds) {
                  final newFilters =
                      selected.copyWith(templateIds: newTemplateIds.toList());
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
              _buildFilterSection(
                context: context,
                label: 'Execution Metadata',
                allValues: filters.executionMetadata.toRows().toList(),
                displayValues: Map.fromEntries(
                  filters.executionMetadata
                      .toRows()
                      .map((v) => MapEntry(v, '${v.$1}: ${v.$2}')),
                ),
                selectedValues: selected.executionMetadata.toRows().toSet(),
                onChanged: (newExecutionMetadata) {
                  final newFilters = selected.copyWith(
                    executionMetadata: ExecutionMetadata.fromRows(
                      newExecutionMetadata.toSet(),
                    ),
                  );
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
              _buildFilterSection(
                context: context,
                label: 'Test Result Statuses',
                allValues: filters.testResultStatuses,
                displayValues: Map.fromEntries(
                  filters.testResultStatuses.map((v) => MapEntry(v, v.name)),
                ),
                selectedValues: selected.testResultStatuses.toSet(),
                onChanged: (newStatuses) {
                  final newFilters = selected.copyWith(
                    testResultStatuses: newStatuses.toList(),
                  );
                  field.didChange(newFilters);
                  onChanged?.call(newFilters);
                },
              ),
            ] else
              Text(
                'No filters available.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
          ],
        );
      },
    );
  }
}
