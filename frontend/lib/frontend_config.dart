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

import 'models/family_name.dart';

class FrontendConfig {
  // Map 'snap' to 'snaps', 'deb' to 'debs', etc
  static final List<String> _validTabs =
      FamilyName.values.map((family) => '${family.name}s').toList();

  final bool requireAuthentication;
  final List<String> tabs;

  FrontendConfig._internal({
    required this.requireAuthentication,
    required this.tabs,
  });

  factory FrontendConfig({
    bool requireAuthentication = false,
    List<String>? tabs,
  }) {
    final bool tabsAreValid =
        tabs != null && tabs.every((tab) => _validTabs.contains(tab));

    // Default to the full set of valid tabs if the provided tabs are invalid or null
    return FrontendConfig._internal(
      requireAuthentication: requireAuthentication,
      tabs: tabsAreValid ? tabs : _validTabs,
    );
  }
}

// This gets loaded at runtime in main.dart
late FrontendConfig frontendConfig;

FrontendConfig parseFrontendConfig(String yamlString) {
  try {
    final decoded = loadYaml(yamlString);
    if (decoded is YamlMap) {
      final config = FrontendConfig(
        requireAuthentication: decoded['require_authentication'] == true,
        tabs: (decoded['tabs'] as YamlList?)
            ?.map((tab) => tab.toString())
            .toList(),
      );
      return config;
    }
  } catch (_) {
    // Fall through to default
  }
  return FrontendConfig();
}

Future<FrontendConfig> loadFrontendConfig() async {
  try {
    final yaml = await rootBundle.loadString('assets/config.yaml');
    final config = parseFrontendConfig(yaml);
    return config;
  } catch (_) {
    // Keep default config
    return FrontendConfig();
  }
}
