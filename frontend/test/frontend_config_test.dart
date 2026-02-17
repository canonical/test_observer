// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/frontend_config.dart';

void main() {
  group('parseFrontendConfig', () {
    test('parses valid single tab', () {
      expect(parseFrontendConfig('tabs:\n  - images'), ['/images']);
    });

    test('parses valid multiple tabs', () {
      expect(
        parseFrontendConfig('tabs:\n  - snaps\n  - debs\n  - charms\n  - images'),
        ['/snaps', '/debs', '/charms', '/images'],
      );
    });

    test('returns null for malformed YAML', () {
      expect(parseFrontendConfig(': [invalid'), isNull);
    });

    test('returns null for invalid family name', () {
      expect(parseFrontendConfig('tabs:\n  - foo'), isNull);
    });

    test('returns null for empty tabs array', () {
      expect(parseFrontendConfig('tabs: []'), isNull);
    });

    test('returns null for plain list YAML', () {
      expect(parseFrontendConfig('- images'), isNull);
    });

    test('returns null for missing tabs key', () {
      expect(parseFrontendConfig('other:\n  - images'), isNull);
    });

    test('returns null when any entry is invalid', () {
      expect(parseFrontendConfig('tabs:\n  - images\n  - invalid'), isNull);
    });

    test('parses subset of tabs', () {
      expect(
        parseFrontendConfig('tabs:\n  - snaps\n  - images'),
        ['/snaps', '/images'],
      );
    });
  });
}
