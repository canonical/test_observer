// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/execution_metadata.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/providers/execution_metadata.dart';
import 'package:testcase_dashboard/ui/page_filters/multi_select_combobox.dart';
import 'package:testcase_dashboard/ui/test_results_page/test_results_filters_view.dart';

Finder stageOption(String label) => find.descendant(
      of: find.byType(MultiSelectCombobox<String>),
      matching: find.text(label),
    );

void main() {
  testWidgets('empty and custom stage values can be selected independently',
      (tester) async {
    var filters = const TestResultsFilters();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          executionMetadataProvider.overrideWith(
            (ref) async => ExecutionMetadata(data: {}),
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: TestResultsFiltersView(
                initialFilters: filters,
                enabledFilters: const {FilterType.artefactStages},
                onChanged: (value) => filters = value,
              ),
            ),
          ),
        ),
      ),
    );
    await tester.tap(find.text('Artefact Stage (0 selected)'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), '(no stage)');
    await tester.pumpAndSettle();
    await tester.tap(stageOption('(no stage)'));
    await tester.pumpAndSettle();
    await tester.tap(stageOption('"(no stage)"'));
    await tester.pumpAndSettle();
    expect(filters.artefactStages, ['', '(no stage)']);
  });
}
