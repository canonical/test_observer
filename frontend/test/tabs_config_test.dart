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
import 'package:testcase_dashboard/tabs_config.dart';

void main() {
  group('parseTabsConfig', () {
    test('parses valid single tab', () {
      expect(parseTabsConfig('["images"]'), ['/images']);
    });

    test('parses valid multiple tabs', () {
      expect(
        parseTabsConfig('["snaps", "debs", "charms", "images"]'),
        ['/snaps', '/debs', '/charms', '/images'],
      );
    });

    test('returns null for malformed JSON', () {
      expect(parseTabsConfig('not json'), isNull);
    });

    test('returns null for invalid family name', () {
      expect(parseTabsConfig('["foo"]'), isNull);
    });

    test('returns null for empty array', () {
      expect(parseTabsConfig('[]'), isNull);
    });

    test('returns null for non-array JSON', () {
      expect(parseTabsConfig('{"tabs": ["images"]}'), isNull);
    });

    test('returns null when any entry is invalid', () {
      expect(parseTabsConfig('["images", "invalid"]'), isNull);
    });

    test('parses subset of tabs', () {
      expect(
        parseTabsConfig('["snaps", "images"]'),
        ['/snaps', '/images'],
      );
    });
  });
}
