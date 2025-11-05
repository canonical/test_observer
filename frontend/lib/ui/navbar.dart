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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher_string.dart';
import 'package:yaru/yaru.dart';

import '../providers/api.dart';
import '../providers/current_user.dart';
import '../routing.dart';
import 'spacing.dart';

const _navbarHeight = 57.0;

class Navbar extends ConsumerWidget {
  const Navbar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(currentUserProvider).valueOrNull;

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
                  const _NavbarEntry(
                    title: 'Search Results',
                    route: AppRoutes.testResults,
                  ),
                  const _NavbarEntry(
                    title: 'Issues',
                    route: '/issues',
                  ),
                  _NavbarDropdownEntry(
                    label: 'Help',
                    dropdownChildren: [
                      _NavbarDropdownItem(
                        label: 'Docs',
                        onPressed: () => launchUrlString(
                          'https://canonical-test-observer.readthedocs-hosted.com/en/latest/',
                        ),
                      ),
                      _NavbarDropdownItem(
                        label: 'Feedback',
                        onPressed: () => launchUrlString(
                          'https://github.com/canonical/test_observer/issues',
                        ),
                      ),
                      _NavbarDropdownItem(
                        label: 'Source Code',
                        onPressed: () => launchUrlString(
                          'https://github.com/canonical/test_observer',
                        ),
                      ),
                    ],
                  ),
                  user == null
                      ? _NavbarButton(
                          title: 'Log in',
                          onTap: () {
                            final uri = Uri.parse(apiUrl);
                            final newUri = uri.replace(
                              path: '/v1/auth/saml/login',
                              queryParameters: {
                                'return_to': Uri.base.toString(),
                              },
                            );
                            launchUrlString(
                              newUri.toString(),
                              webOnlyWindowName: '_self',
                            );
                          },
                        )
                      : _NavbarDropdownEntry(
                          label: 'hi ${user.name}',
                          dropdownChildren: [
                            _NavbarDropdownItem(
                              label: 'Log out',
                              onPressed: () {
                                final uri = Uri.parse(apiUrl);
                                final newUri = uri.replace(
                                  path: '/v1/auth/saml/logout',
                                  queryParameters: {
                                    'return_to': Uri.base.toString(),
                                  },
                                );
                                launchUrlString(
                                  newUri.toString(),
                                  webOnlyWindowName: '_self',
                                );
                              },
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
          child: Padding(
            padding: const EdgeInsets.all(Spacing.level4),
            child: Text(
              label,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.apply(color: Colors.white),
            ),
          ),
        ),
      ),
    );
  }
}

class _NavbarDropdownItem extends StatelessWidget {
  const _NavbarDropdownItem({required this.label, this.onPressed});

  final String label;
  final void Function()? onPressed;

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

class _NavbarButton extends StatelessWidget {
  const _NavbarButton({required this.title, this.onTap});

  final String title;
  final void Function()? onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
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
