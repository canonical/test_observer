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
import 'package:testcase_dashboard/models/user.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/current_user.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/artefact_page/artefact_delete_button.dart';

import '../../dummy_data.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

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

  testWidgets('deletes the artefact and navigates to its dashboard',
      (tester) async {
    final api = ApiRepositoryMock();
    when(() => api.getArtefact(1)).thenAnswer((_) async => dummyArtefact);
    when(() => api.deleteArtefact(1)).thenAnswer((_) async {});

    await pumpDeleteButtonWithApi(tester, api);

    await tester.tap(find.text('Delete'));
    await tester.pumpAndSettle();
    expect(find.text('Delete artefact?'), findsOneWidget);

    await tester.tap(
      find.descendant(
        of: find.byType(AlertDialog),
        matching: find.text('Delete'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Dashboard'), findsOneWidget);
    verify(() => api.deleteArtefact(1)).called(1);
  });

  testWidgets('shows an error and stays on the artefact page when delete fails',
      (tester) async {
    final api = ApiRepositoryMock();
    when(() => api.getArtefact(1)).thenAnswer((_) async => dummyArtefact);
    when(() => api.deleteArtefact(1)).thenThrow(StateError('offline'));

    await pumpDeleteButtonWithApi(tester, api);

    await tester.tap(find.text('Delete'));
    await tester.pumpAndSettle();
    expect(find.text('Delete artefact?'), findsOneWidget);

    await tester.tap(
      find.descendant(
        of: find.byType(AlertDialog),
        matching: find.text('Delete'),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('Could not delete artefact'), findsOneWidget);
    expect(find.text('Artefact page'), findsOneWidget);
    expect(find.text('Dashboard'), findsNothing);
    expect(find.text('Delete'), findsOneWidget);
    verify(() => api.deleteArtefact(1)).called(1);
  });
}

Future<void> pumpDeleteButtonWithApi(
  WidgetTester tester,
  ApiRepository api,
) async {
  final router = GoRouter(
    initialLocation: '/snaps/1',
    routes: [
      GoRoute(
        path: '/snaps',
        builder: (context, state) => const Scaffold(
          body: Text('Dashboard'),
        ),
      ),
      GoRoute(
        path: '/snaps/:artefactId',
        builder: (context, state) => Scaffold(
          body: Column(
            children: [
              const Text('Artefact page'),
              ArtefactDeleteButton(
                artefactId: int.parse(state.pathParameters['artefactId']!),
              ),
            ],
          ),
        ),
      ),
    ],
  );

  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiProvider.overrideWith((ref) => api),
        currentUserProvider.overrideWith(
          (ref) async => const User(
            id: 1,
            name: 'Admin',
            email: 'admin@example.com',
            isAdmin: true,
          ),
        ),
      ],
      child: MaterialApp.router(routerConfig: router),
    ),
  );
  await tester.pumpAndSettle();
}
