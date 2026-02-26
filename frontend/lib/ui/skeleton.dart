// Copyright 2023 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';

import 'dashboard/find_shortcut.dart';
import 'error_popup.dart';
import 'navbar.dart';
import 'spacing.dart';

class Skeleton extends StatelessWidget {
  const Skeleton({super.key, required this.body});

  final Widget body;

  @override
  Widget build(BuildContext context) {
    return FindShortcut(
      child: SelectionArea(
        child: Scaffold(
          body: ErrorPopup(
            child: Column(
              children: [
                const Navbar(),
                Expanded(
                  child: ConstrainedBox(
                    constraints: BoxConstraints.loose(
                      const Size.fromWidth(Spacing.maxPageContentWidth),
                    ),
                    child: body,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
