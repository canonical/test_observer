// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'dart:collection';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';
import 'package:testcase_dashboard/providers/filtered_family_artefacts.dart';
import 'package:testcase_dashboard/routing.dart';
import 'package:testcase_dashboard/ui/dashboard/dashboard_body/artefacts_columns_view.dart';

import '../dummy_data.dart';

void main() {
  testWidgets('dashboard displays a column for a custom stage', (tester) async {
    final uri = Uri(path: AppRoutes.snaps);
    final artefact = dummyArtefact.copyWith(stage: 'custom');
    final router = GoRouter(
      initialLocation: uri.toString(),
      routes: [
        GoRoute(
          path: AppRoutes.snaps,
          builder: (_, __) => const Scaffold(body: ArtefactsColumnsView()),
        ),
      ],
    );
    addTearDown(router.dispose);

    await tester.pumpWidget(
      ProviderScope(
        overrides: [
          filteredFamilyArtefactsProvider(uri).overrideWith(
            (ref) => LinkedHashMap.of({artefact.id: artefact}),
          ),
        ],
        child: MaterialApp.router(routerConfig: router),
      ),
    );
    await tester.pumpAndSettle();
    await tester.drag(
      find.byType(ArtefactsColumnsView),
      const Offset(-1600, 0),
    );
    await tester.pumpAndSettle();
    expect(find.text('Custom'), findsOneWidget);
    expect(find.text(artefact.name), findsOneWidget);
  });
}
