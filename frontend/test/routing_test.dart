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

import 'package:flutter_test/flutter_test.dart';

import 'package:testcase_dashboard/routing.dart';

void main() {
  group('getAuthenticationRedirect', () {
    test('returns null when authentication is not required', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: false,
        isAuthenticated: false,
        destinationUri: Uri.parse('/snaps'),
      );

      expect(redirect, isNull);
    });

    test('redirects unauthenticated users to login prompt', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: true,
        isAuthenticated: false,
        destinationUri: Uri.parse('/issues'),
      );

      expect(redirect, '/login?returnTo=%2Fissues');
    });

    test('does not redirect when already on login prompt', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: true,
        isAuthenticated: false,
        destinationUri: Uri.parse('/login?returnTo=%2Fissues'),
      );

      expect(redirect, isNull);
    });

    test('sends authenticated user from login prompt to returnTo path', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: true,
        isAuthenticated: true,
        destinationUri: Uri.parse('/login?returnTo=%2Fnotifications'),
      );

      expect(redirect, '/notifications');
    });

    test('drops unsafe returnTo values and redirects to root', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: true,
        isAuthenticated: true,
        destinationUri: Uri.parse('/login?returnTo=https://example.com/path'),
      );

      expect(redirect, '/');
    });

    test('drops protocol-relative returnTo values and redirects to root', () {
      final redirect = getAuthenticationRedirect(
        requireAuthentication: true,
        isAuthenticated: true,
        destinationUri: Uri.parse('/login?returnTo=%2F%2Fevil.example%2Fpath'),
      );

      expect(redirect, '/');
    });
  });
}
