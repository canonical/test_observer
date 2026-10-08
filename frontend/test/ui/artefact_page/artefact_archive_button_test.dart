// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:testcase_dashboard/models/artefact.dart';
import 'package:testcase_dashboard/models/user.dart';
import 'package:testcase_dashboard/providers/api.dart';
import 'package:testcase_dashboard/providers/artefact.dart'
    as artefact_provider;
import 'package:testcase_dashboard/providers/current_user.dart';
import 'package:testcase_dashboard/repositories/api_repository.dart';
import 'package:testcase_dashboard/ui/artefact_page/artefact_archive_button.dart';

import '../../dummy_data.dart';

class ApiRepositoryMock extends Mock implements ApiRepository {}

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

  testWidgets('shows Archive for a user with change permission',
      (tester) async {
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

  testWidgets('updates the archived state after a successful PATCH',
      (tester) async {
    final api = ApiRepositoryMock();
    final patchCompleter = Completer<Artefact>();
    when(() => api.getArtefact(1))
        .thenAnswer((_) async => dummyArtefact.copyWith(archived: false));
    when(() => api.setArtefactArchived(1, true))
        .thenAnswer((_) => patchCompleter.future);

    await pumpReactiveArchiveButton(tester, api);

    await tester.tap(find.text('Archive'));
    await tester.pump();

    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    expect(find.text('Archive'), findsNothing);
    expect(
      tester.widget<TextButton>(find.byType(TextButton)).onPressed,
      isNull,
    );

    patchCompleter.complete(dummyArtefact.copyWith(archived: true));
    await tester.pumpAndSettle();

    expect(find.text('Unarchive'), findsOneWidget);
    verify(() => api.setArtefactArchived(1, true)).called(1);
  });

  testWidgets('shows an error notification when PATCH fails', (tester) async {
    final api = ApiRepositoryMock();
    when(() => api.getArtefact(1))
        .thenAnswer((_) async => dummyArtefact.copyWith(archived: false));
    when(() => api.setArtefactArchived(1, true))
        .thenThrow(StateError('offline'));

    await pumpReactiveArchiveButton(tester, api);

    await tester.tap(find.text('Archive'));
    await tester.pumpAndSettle();

    expect(find.textContaining('Could not archive artefact'), findsOneWidget);
    expect(find.text('Archive'), findsOneWidget);
    expect(find.byType(CircularProgressIndicator), findsNothing);
    verify(() => api.setArtefactArchived(1, true)).called(1);
  });
}

Future<void> pumpReactiveArchiveButton(
  WidgetTester tester,
  ApiRepository api,
) async {
  await tester.pumpWidget(
    ProviderScope(
      overrides: [
        apiProvider.overrideWith((ref) => api),
        currentUserProvider.overrideWith(
          (ref) async => const User(
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
        ),
      ],
      child: const MaterialApp(
        home: Scaffold(
          body: _ReactiveArchiveButtonHarness(),
        ),
      ),
    ),
  );
  await tester.pumpAndSettle();
}

class _ReactiveArchiveButtonHarness extends ConsumerWidget {
  const _ReactiveArchiveButtonHarness();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefact = ref.watch(artefact_provider.artefactProvider(1));
    return artefact.when(
      data: (artefact) => ArtefactArchiveButton(
        artefactId: artefact.id,
        archived: artefact.archived,
      ),
      loading: () => const CircularProgressIndicator(),
      error: (error, stackTrace) => Text('Failed to load artefact: $error'),
    );
  }
}
