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

import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../routing.dart';
import 'vanilla/vanilla_navigation.dart';

class Navbar extends StatelessWidget {
  const Navbar({super.key});

  @override
  Widget build(BuildContext context) {
    return VanillaNavigation(
      children: [
        VanillaNavigationTitle(
          title: 'Canonical Test Observer',
          onPressed: () => context.go('/'),
        ),
        const _NavbarEntry(title: 'Snap Testing', route: AppRoutes.snaps),
        const _NavbarEntry(title: 'Deb Testing', route: AppRoutes.debs),
        const _NavbarEntry(title: 'Charm Testing', route: AppRoutes.charms),
        const _NavbarEntry(title: 'Image Testing', route: AppRoutes.images),
        VanillaNavigationDropdown(
          menuChildren: [
            VanillaNavigationButton(
              child: const Text('Source Code'),
              onPressed: () =>
                  launchUrlString('https://github.com/canonical/test_observer'),
            ),
          ],
          child: const Text('Help'),
        ),
      ],
    );
  }
}

class _NavbarEntry extends StatelessWidget {
  const _NavbarEntry({required this.route, required this.title});

  final String route;
  final String title;

  @override
  Widget build(BuildContext context) {
    return VanillaNavigationButton(
      isSelected: GoRouterState.of(context).fullPath!.startsWith(route),
      onPressed: () => context.go(route),
      child: Text(title),
    );
  }
}
