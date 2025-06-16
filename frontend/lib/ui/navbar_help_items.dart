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
import 'package:url_launcher/url_launcher_string.dart';

const _navbarHeight = 57.0;

class NavbarHelpItem extends StatelessWidget {
  const NavbarHelpItem({required this.label, required this.url, super.key});

  final String label;
  final String url;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: _navbarHeight,
      child: MenuItemButton(
        onPressed: () => launchUrlString(url),
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