// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart' hide Family;
import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/execution_metadata.dart';
import 'package:testcase_dashboard/models/family.dart';
import 'package:testcase_dashboard/models/test_results_filters.dart';
import 'package:testcase_dashboard/providers/execution_metadata.dart';
import 'package:testcase_dashboard/providers/families.dart';
import 'package:testcase_dashboard/ui/test_results_page/test_results_filters_view.dart';

void main() {
  testWidgets('family loading, error and success preserve selections',
      (tester) async {
    var pending = Completer<List<Family>>();
    late WidgetRef widgetRef;
    TestResultsFilters? applied;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          familiesProvider.overrideWith((ref) => pending.future),
          executionMetadataProvider.overrideWith(
            (ref) async => ExecutionMetadata(data: {}),
          ),
        ],
        child: MaterialApp(
          home: Scaffold(
            body: Consumer(
              builder: (context, ref, child) {
                widgetRef = ref;
                return TestResultsFiltersView(
                  initialFilters: const TestResultsFilters(families: ['alpha']),
                  enabledFilters: const {
                    FilterType.families,
                    FilterType.testResultStatuses,
                  },
                  onApplyFilters: (filters) => applied = filters,
                );
              },
            ),
          ),
        ),
      ),
    );
    expect(find.text('Loading families...'), findsOneWidget);
    expect(find.text('alpha'), findsOneWidget);
    expect(find.text('Status (0 selected)'), findsOneWidget);

    pending.completeError(StateError('unavailable'));
    await tester.pumpAndSettle();
    expect(find.text('Could not load families'), findsOneWidget);
    expect(find.text('alpha'), findsOneWidget);

    pending = Completer<List<Family>>();
    widgetRef.invalidate(familiesProvider);
    await tester.pump();
    expect(find.text('Loading families...'), findsOneWidget);
    pending.complete([const Family(name: 'alpha'), const Family(name: 'beta')]);
    await tester.pumpAndSettle();
    expect(find.text('Loading families...'), findsNothing);
    expect(find.text('Could not load families'), findsNothing);
    expect(find.text('alpha'), findsOneWidget);
    expect(find.text('beta'), findsOneWidget);

    // A successful empty response is distinct from loading or failure.
    pending = Completer<List<Family>>();
    widgetRef.invalidate(familiesProvider);
    await tester.pump();
    pending.complete([]);
    await tester.pumpAndSettle();
    expect(find.text('No families available'), findsOneWidget);
    expect(find.text('alpha'), findsOneWidget);
    expect(find.text('Status (0 selected)'), findsOneWidget);
    await tester.tap(find.text('Apply Filters'));
    expect(applied?.families, ['alpha']);
  });
}
