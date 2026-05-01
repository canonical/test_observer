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
import 'package:testcase_dashboard/ui/login.dart';
import 'package:flutter/material.dart';

void main() {
  group('buildFrontendReturnToUrl', () {
    test('preserves hash routing when base uri uses fragment routes', () {
      final returnTo = buildFrontendReturnToUrl(
        baseUri:
            Uri.parse('http://localhost:30001/#/login?returnTo=/test-results'),
        localPath: '/test-results',
      );

      expect(returnTo, 'http://localhost:30001/#/test-results');
    });

    test('uses path routing when base uri does not use hash routes', () {
      final returnTo = buildFrontendReturnToUrl(
        baseUri:
            Uri.parse('http://localhost:30001/login?returnTo=/test-results'),
        localPath: '/test-results',
      );

      expect(returnTo, 'http://localhost:30001/test-results');
    });

    test('falls back to root for unsafe local path', () {
      final returnTo = buildFrontendReturnToUrl(
        baseUri: Uri.parse('http://localhost:30001/#/login'),
        localPath: 'https://example.com/escape',
      );

      expect(returnTo, 'http://localhost:30001/#/');
    });
  });

  group('LoginPromptPage', () {
    testWidgets('renders login prompt content', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: LoginPromptPage(),
        ),
      );

      expect(find.text('Login required'), findsOneWidget);
      expect(
        find.text('You need to log in before accessing this page.'),
        findsOneWidget,
      );
      expect(find.text('Log in'), findsOneWidget);
      expect(find.byType(FilledButton), findsOneWidget);
    });

    testWidgets('accepts an internal returnTo path', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: LoginPromptPage(returnTo: '/test-results'),
        ),
      );

      expect(find.byType(LoginPromptPage), findsOneWidget);
    });
  });
}
