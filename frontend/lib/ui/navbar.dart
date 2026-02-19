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
import '../frontend_config.dart';
import 'spacing.dart';

const _navbarHeight = 57.0;
final _navbarSelectedColor = YaruColors.titleBarDark.scale(lightness: 0.07);

TextStyle? _navbarTextStyle(BuildContext context) {
  return Theme.of(context).textTheme.titleMedium?.apply(color: Colors.white);
}

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
            Image.asset(
              'assets/logo.png',
              filterQuality: FilterQuality.high,
              errorBuilder: (context, error, stackTrace) =>
                  const SizedBox.shrink(),
              frameBuilder: (context, child, frame, wasSynchronouslyLoaded) {
                if (wasSynchronouslyLoaded || frame != null) {
                  return Row(
                    children: [
                      child,
                      const SizedBox(width: Spacing.level4),
                    ],
                  );
                }
                return const SizedBox.shrink();
              },
            ),
            Expanded(
              child: Row(
                children: [
                  ...configuredTabs.map(
                    (route) => _NavbarEntry(
                      title: familyDisplayName(route),
                      route: route,
                    ),
                  ),
                  const Spacer(),
                  const _NavbarEntry(
                    title: 'Search',
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
                          label: user.name,
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
              style: _navbarTextStyle(context),
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
          style: _navbarTextStyle(context),
        ),
      ),
    );
  }
}

class _NavbarEntry extends StatefulWidget {
  const _NavbarEntry({required this.route, required this.title});

  final String route;
  final String title;

  @override
  State<_NavbarEntry> createState() => _NavbarEntryState();
}

class _NavbarEntryState extends State<_NavbarEntry> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isSelected =
        GoRouterState.of(context).fullPath!.startsWith(widget.route);

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      child: InkWell(
        onTap: () => context.go(widget.route),
        child: Container(
          decoration: (isSelected || _isHovered)
              ? BoxDecoration(
                  color: _navbarSelectedColor,
                  border: isSelected
                      ? const Border(
                          bottom: BorderSide(color: Colors.white, width: 2),
                        )
                      : null,
                )
              : null,
          padding: const EdgeInsets.all(Spacing.level4),
          child: Text(
            widget.title,
            style: _navbarTextStyle(context),
          ),
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
          style: _navbarTextStyle(context),
        ),
      ),
    );
  }
}
