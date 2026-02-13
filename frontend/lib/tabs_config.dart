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

import 'dart:convert';

import 'package:flutter/services.dart';

import 'routing.dart';

const _validTabs = {'snaps', 'debs', 'charms', 'images'};

List<String> configuredTabs = [
  AppRoutes.snaps,
  AppRoutes.debs,
  AppRoutes.charms,
  AppRoutes.images,
];

String familyDisplayName(String route) {
  switch (route) {
    case AppRoutes.snaps:
      return 'Snap Testing';
    case AppRoutes.debs:
      return 'Deb Testing';
    case AppRoutes.charms:
      return 'Charm Testing';
    case AppRoutes.images:
      return 'Image Testing';
    default:
      return '';
  }
}

List<String>? parseTabsConfig(String jsonString) {
  try {
    final decoded = jsonDecode(jsonString);
    if (decoded is! List || decoded.isEmpty) return null;

    final tabs = decoded.cast<String>();
    if (!tabs.every((t) => _validTabs.contains(t))) return null;

    return tabs.map((t) => '/$t').toList();
  } catch (_) {
    return null;
  }
}

Future<void> loadTabsConfig() async {
  try {
    final json = await rootBundle.loadString('assets/tabs_config.json');
    final parsed = parseTabsConfig(json);
    if (parsed != null) {
      configuredTabs = parsed;
    }
  } catch (_) {
    // Keep default config
  }
}
