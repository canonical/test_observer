// Copyright 2026 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/user.dart';

void main() {
  group('User.canDeleteArtefact', () {
    test('is true for admins', () {
      final user = User(
        id: 1,
        name: 'Admin User',
        email: 'admin@example.com',
        isAdmin: true,
      );

      expect(user.canDeleteArtefact, isTrue);
    });

    test('is true when a team grants delete_artefact', () {
      final user = User(
        id: 1,
        name: 'Team User',
        email: 'team@example.com',
        teams: const [
          UserTeam(
            id: 1,
            name: 'deletion team',
            permissions: ['delete_artefact'],
          ),
        ],
      );

      expect(user.canDeleteArtefact, isTrue);
    });

    test('is false without the permission or admin status', () {
      final user = User(
        id: 1,
        name: 'Regular User',
        email: 'user@example.com',
        teams: const [UserTeam(id: 1, name: 'read-only team')],
      );

      expect(user.canDeleteArtefact, isFalse);
    });

    test('parses admin and team permissions from the current-user response',
        () {
      final user = User.fromJson({
        'id': 1,
        'name': 'Admin User',
        'email': 'admin@example.com',
        'is_admin': false,
        'teams': [
          {
            'id': 1,
            'name': 'deletion team',
            'permissions': ['delete_artefact'],
          },
        ],
      });

      expect(user.canDeleteArtefact, isTrue);
    });
  });
}
