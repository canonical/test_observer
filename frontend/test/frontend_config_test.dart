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
import 'package:testcase_dashboard/frontend_config.dart';
import 'package:testcase_dashboard/models/family_name.dart';

void main() {
  group('parseFrontendConfig', () {
    final allTabs =
        FamilyName.values.map((family) => '${family.name}s').toList();

    test('defaults for empty config', () {
      final config = parseFrontendConfig('');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('parses complete config', () {
      final config = parseFrontendConfig(
        'require_authentication: true\ntabs:\n  - snaps\n  - debs',
      );

      expect(config.requireAuthentication, isTrue);
      expect(config.tabs, ['snaps', 'debs']);
    });

    test('parses only require_authentication', () {
      final config = parseFrontendConfig('require_authentication: true');

      expect(config.requireAuthentication, isTrue);
      expect(config.tabs, allTabs);
    });

    test('parses valid single tab', () {
      final config = parseFrontendConfig('tabs:\n  - images');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, ['images']);
    });

    test('parses valid multiple tabs', () {
      final config = parseFrontendConfig(
        'tabs:\n  - snaps\n  - debs\n  - charms\n  - images',
      );

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, ['snaps', 'debs', 'charms', 'images']);
    });

    test('defaults for malformed YAML', () {
      final config = parseFrontendConfig(': [invalid');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('defaults for invalid family name', () {
      final config = parseFrontendConfig('tabs:\n  - foo');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('accepts empty tabs array', () {
      final config = parseFrontendConfig('tabs: []');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, <String>[]);
    });

    test('defaults for plain list YAML', () {
      final config = parseFrontendConfig('- images');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('defaults tabs for missing tabs key', () {
      final config = parseFrontendConfig('other:\n  - images');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('defaults tabs when any entry is invalid', () {
      final config = parseFrontendConfig('tabs:\n  - images\n  - invalid');

      expect(config.requireAuthentication, isFalse);
      expect(config.tabs, allTabs);
    });

    test('parses require_authentication', () {
      final config = parseFrontendConfig(
        'require_authentication: true\ntabs:\n  - images',
      );

      expect(config.requireAuthentication, isTrue);
      expect(config.tabs, ['images']);
    });

    test('preserves require_authentication when tabs has an invalid type', () {
      final config = parseFrontendConfig(
        'require_authentication: true\ntabs: snaps',
      );
      expect(config.requireAuthentication, isTrue);
      expect(config.tabs, allTabs);
    });
  });
}
