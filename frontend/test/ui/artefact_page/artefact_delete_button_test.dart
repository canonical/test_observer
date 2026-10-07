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
import 'package:testcase_dashboard/models/user.dart';
import 'package:testcase_dashboard/providers/current_user.dart';
import 'package:testcase_dashboard/ui/artefact_page/artefact_delete_button.dart';

void main() {
  Future<void> pumpDeleteButton(WidgetTester tester, User? user) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [currentUserProvider.overrideWith((ref) async => user)],
        child: const MaterialApp(
          home: Scaffold(
            body: ArtefactDeleteButton(artefactId: 1),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('hides the button when the user lacks permission',
      (tester) async {
    await pumpDeleteButton(
      tester,
      const User(id: 1, name: 'User', email: 'user@example.com'),
    );

    expect(find.text('Delete'), findsNothing);
  });

  testWidgets('shows the button for a team permission grant', (tester) async {
    await pumpDeleteButton(
      tester,
      const User(
        id: 1,
        name: 'User',
        email: 'user@example.com',
        teams: [
          UserTeam(
            id: 1,
            name: 'deletion team',
            permissions: ['delete_artefact'],
          ),
        ],
      ),
    );

    expect(find.text('Delete'), findsOneWidget);
  });

  testWidgets('shows the button for an admin', (tester) async {
    await pumpDeleteButton(
      tester,
      const User(
        id: 1,
        name: 'Admin',
        email: 'admin@example.com',
        isAdmin: true,
      ),
    );

    expect(find.text('Delete'), findsOneWidget);
  });

  testWidgets('requires confirmation and allows cancellation', (tester) async {
    await pumpDeleteButton(
      tester,
      const User(
        id: 1,
        name: 'Admin',
        email: 'admin@example.com',
        isAdmin: true,
      ),
    );

    await tester.tap(find.text('Delete'));
    await tester.pumpAndSettle();
    expect(find.text('Delete artefact?'), findsOneWidget);

    await tester.tap(find.text('Cancel'));
    await tester.pumpAndSettle();
    expect(find.text('Delete artefact?'), findsNothing);
    expect(find.text('Delete'), findsOneWidget);
  });
}
