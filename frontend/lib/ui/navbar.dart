// Copyright (C) 2024 Canonical Ltd.
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
import 'package:yaru/yaru.dart';

import '../routing.dart';
import 'spacing.dart';

class Navbar extends StatelessWidget {
  const Navbar({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: Spacing.pageHorizontalPadding,
      ),
      color: YaruColors.coolGrey,
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Image.asset('assets/canonical.png'),
          const SizedBox(width: Spacing.level4),
          const Expanded(
            child: Row(
              children: [
                _NavbarEntry(title: 'Snap Testing', route: AppRoutes.snaps),
                _NavbarEntry(title: 'Deb Testing', route: AppRoutes.debs),
                _NavbarEntry(title: 'Charm Testing', route: AppRoutes.charms),
                _NavbarEntry(title: 'Image Testing', route: AppRoutes.images),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _NavbarEntry extends StatelessWidget {
  const _NavbarEntry({required this.route, required this.title});

  final String route;
  final String title;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => context.go(route),
      child: Container(
        color: GoRouterState.of(context).fullPath!.startsWith(route)
            ? YaruColors.orange
            : null,
        padding: const EdgeInsets.all(Spacing.level4),
        child: Text(
          title,
          style: Theme.of(context)
              .textTheme
              .titleLarge
              ?.apply(color: Colors.white),
        ),
      ),
    );
  }
}
