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

// frontend/assets/config.yaml
//
// This configuration files allows to pass configuration option to test_observer
// Frontend that should be processed while rendering the front page and
// preferably at Runtime.
//
// tabs:
//   This section allows to specify which Testing tabs will show on a
//   test_observer instance and in which order
//
//   The possible tabs at this point in time are:
//     - images, snaps, debs and charms
//
// The correct syntaxt is as follow if you want to see all the tabs:
// tabs:
//   - images
//   - snaps
//   - debs
//   - charms

import 'package:flutter/services.dart';
import 'package:yaml/yaml.dart';

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

List<String>? parseFrontendConfig(String yamlString) {
  try {
    final decoded = loadYaml(yamlString);
    if (decoded is! YamlMap) return null;

    final tabs = decoded['tabs'];
    if (tabs is! YamlList || tabs.isEmpty) return null;

    final tabStrings = tabs.cast<String>();
    if (!tabStrings.every((t) => _validTabs.contains(t))) return null;

    return tabStrings.map<String>((t) => '/$t').toList();
  } catch (_) {
    return null;
  }
}

Future<void> loadFrontendConfig() async {
  try {
    final yaml = await rootBundle.loadString('assets/config.yaml');
    final parsed = parseFrontendConfig(yaml);
    if (parsed != null) {
      configuredTabs = parsed;
    }
  } catch (_) {
    // Keep default config
  }
}
