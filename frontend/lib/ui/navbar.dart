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
import 'package:yaru/yaru.dart';

import '../routing.dart';
import 'spacing.dart';
import 'navbar_help_items.dart';

const _navbarHeight = 57.0;

class Navbar extends StatelessWidget {
  const Navbar({super.key});

  void _navigateWithDelay(BuildContext context, String route) {
    // Use a timer to delay navigation until after the dropdown closes
    Future.delayed(const Duration(milliseconds: 150), () {
      if (context.mounted) {
        context.go(route);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: YaruColors.coolGrey,
      alignment: Alignment.center,
      height: _navbarHeight,
      child: Container(
        constraints: BoxConstraints.loose(
          const Size.fromWidth(Spacing.maxPageContentWidth),
        ),
        padding: const EdgeInsets.symmetric(
          horizontal: Spacing.pageHorizontalPadding,
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Image.asset('assets/canonical.png'),
            const SizedBox(width: Spacing.level4),
            Expanded(
              child: Row(
                children: [
                  const _NavbarEntry(
                    title: 'Snap Testing',
                    route: AppRoutes.snaps,
                  ),
                  const _NavbarEntry(
                    title: 'Deb Testing',
                    route: AppRoutes.debs,
                  ),
                  const _NavbarEntry(
                    title: 'Charm Testing',
                    route: AppRoutes.charms,
                  ),
                  const _NavbarEntry(
                    title: 'Image Testing',
                    route: AppRoutes.images,
                  ),
                  const Spacer(),
                  _NavbarDropdownEntry(
                    label: 'Reports',
                    dropdownChildren: [
                      _NavbarDropdownItem(
                        label: 'Test Summary',
                        onPressed: () => _navigateWithDelay(context, AppRoutes.testSummaryReport),
                      ),
                      _NavbarDropdownItem(
                        label: 'Test Case Issues',
                        onPressed: () => _navigateWithDelay(context, AppRoutes.knownIssuesReport),
                      ),
                      _NavbarDropdownItem(
                        label: 'Environment Issues',
                        onPressed: () => _navigateWithDelay(context, AppRoutes.environmentIssuesReport),
                      ),
                    ],
                  ),
                  const _NavbarDropdownEntry(
                    label: 'Help',
                    dropdownChildren: [
                      NavbarHelpItem(
                        label: 'Docs',
                        url: 'https://canonical-test-observer.readthedocs-hosted.com/en/latest/',
                      ),
                      NavbarHelpItem(
                        label: 'Source Code',
                        url: 'https://github.com/canonical/test_observer',
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavbarDropdownEntry extends StatelessWidget {
  const _NavbarDropdownEntry({
    required this.dropdownChildren,
    required this.label,
  });

  final String label;
  final List<Widget> dropdownChildren;

  @override
  Widget build(BuildContext context) {
    return IntrinsicWidth(
      child: SizedBox(
        height: _navbarHeight,
        child: SubmenuButton(
          menuStyle: const MenuStyle(
            shape: WidgetStatePropertyAll(RoundedRectangleBorder()),
            backgroundColor: WidgetStatePropertyAll(YaruColors.coolGrey),
          ),
          menuChildren: dropdownChildren,
          child: Text(
            label,
            style: Theme.of(context)
                .textTheme
                .titleLarge
                ?.apply(color: Colors.white),
          ),
        ),
      ),
    );
  }
}

class _NavbarDropdownItem extends StatelessWidget {
  const _NavbarDropdownItem({required this.label, this.onPressed});

  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: _navbarHeight,
      child: MenuItemButton(
        onPressed: onPressed,
        child: Text(
          label,
          style: Theme.of(context)
              .textTheme
              .titleLarge
              ?.apply(color: Colors.white),
        ),
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
