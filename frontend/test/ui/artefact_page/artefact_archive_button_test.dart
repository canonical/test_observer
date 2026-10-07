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
import 'package:testcase_dashboard/ui/artefact_page/artefact_archive_button.dart';

void main() {
  Future<void> pumpArchiveButton(
    WidgetTester tester, {
    required User? user,
    required bool archived,
  }) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [currentUserProvider.overrideWith((ref) async => user)],
        child: MaterialApp(
          home: Scaffold(
            body: ArtefactArchiveButton(
              artefactId: 1,
              archived: archived,
            ),
          ),
        ),
      ),
    );
    await tester.pumpAndSettle();
  }

  testWidgets('shows Archive for a user with change permission', (tester) async {
    await pumpArchiveButton(
      tester,
      user: const User(
        id: 1,
        name: 'User',
        email: 'user@example.com',
        teams: [
          UserTeam(
            id: 1,
            name: 'edit team',
            permissions: ['change_artefact'],
          ),
        ],
      ),
      archived: false,
    );

    expect(find.text('Archive'), findsOneWidget);
    expect(find.text('Unarchive'), findsNothing);
  });

  testWidgets('shows Unarchive for an admin when archived', (tester) async {
    await pumpArchiveButton(
      tester,
      user: const User(
        id: 1,
        name: 'Admin',
        email: 'admin@example.com',
        isAdmin: true,
      ),
      archived: true,
    );

    expect(find.text('Unarchive'), findsOneWidget);
    expect(find.text('Archive'), findsNothing);
  });

  testWidgets('hides the button without change permission', (tester) async {
    await pumpArchiveButton(
      tester,
      user: const User(id: 1, name: 'User', email: 'user@example.com'),
      archived: false,
    );

    expect(find.text('Archive'), findsNothing);
    expect(find.text('Unarchive'), findsNothing);
  });
}