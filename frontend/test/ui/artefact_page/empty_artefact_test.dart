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
import 'package:go_router/go_router.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/enriched_test_execution.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/current_user.dart';
import 'package:testcase_dashboard/providers/filtered_artefact_environments.dart';
import 'package:testcase_dashboard/providers/filtered_enriched_test_executions.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/artefact_page/artefact_page_body.dart';
import 'package:testcase_dashboard/ui/artefact_page/artefact_signoff_button.dart';
import 'package:testcase_dashboard/ui/artefact_page/bulk_environment_selection_controls.dart';
import 'package:testcase_dashboard/ui/artefact_page/rerun_filtered_plans_button.dart';

import '../../dummy_data.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

void main() {
  testWidgets('empty artefacts show an empty state and cannot rerun plans',
      (tester) async {
    tester.view.physicalSize = const Size(1600, 1000);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await pumpArtefactWidget(
      tester,
      ArtefactPageBody(
        artefact: dummyArtefact.copyWith(allEnvironmentReviewsCount: 0),
      ),
    );

    expect(find.text('No test executions to display.'), findsOneWidget);
    expect(find.byType(BulkEnvironmentSelectionControls), findsNothing);
    final rerunButton = tester.widget<TextButton>(
      find.widgetWithText(TextButton, 'Rerun 0 Filtered Test Plans'),
    );
    expect(rerunButton.onPressed, isNull);
  });

  testWidgets('artefacts with executions can still request reruns',
      (tester) async {
    await pumpArtefactWidget(
      tester,
      const RerunFilteredPlansButton(),
      executions: [
        EnrichedTestExecution(
          testExecution: dummyTestExecution,
          environmentReview: dummyEnvironmentReview,
        ),
      ],
    );

    await tester.tap(find.text('Rerun 1 Filtered Test Plans'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertDialog), findsOneWidget);
    expect(find.text(dummyTestExecution.environment.name), findsOneWidget);
  });

  for (final reviewCount in [0, 1]) {
    testWidgets('approval is available with $reviewCount reviews',
        (tester) async {
      await pumpArtefactWidget(
        tester,
        ArtefactSignoffButton(
          artefact: dummyArtefact.copyWith(
            allEnvironmentReviewsCount: reviewCount,
          ),
        ),
      );

      await tester.tap(find.text('Undecided'));
      await tester.pumpAndSettle();

      final approvalItem = tester.widget<PopupMenuItem<ArtefactStatus>>(
        find.widgetWithText(PopupMenuItem<ArtefactStatus>, 'Approved'),
      );
      expect(approvalItem.enabled, isTrue);
      final approvalLabel = tester.widget<Text>(find.text('Approved'));
      expect(
        approvalLabel.style?.color,
        ArtefactStatus.approved.color,
      );
    });
  }
}

Future<void> pumpArtefactWidget(
  WidgetTester tester,
  Widget child, {
  List<EnrichedTestExecution> executions = const [],
}) async {
  final api = ApiRepositoryMock();
  when(() => api.getArtefactBuilds(1)).thenAnswer((_) async => []);
  final pageUri = Uri.parse('/snaps/1');
  final router = GoRouter(
    initialLocation: pageUri.toString(),
    routes: [
      GoRoute(
        path: '/snaps/:artefactId',
        builder: (_, __) => Scaffold(body: child),
      ),
    ],
  );
  addTearDown(router.dispose);

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiProvider.overrideWith((ref) => api),
        currentUserProvider.overrideWith((ref) async => null),
        filteredArtefactEnvironmentsProvider(pageUri)
            .overrideWith((ref) async => []),
        filteredEnrichedTestExecutionsProvider(pageUri)
            .overrideWith((ref) async => executions),
      ],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
}
