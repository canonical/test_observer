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

import 'spacing.dart';

class Expandable extends StatelessWidget {
  const Expandable({
    super.key,
    required this.title,
    required this.children,
    this.initiallyExpanded = false,
  });

  final List<Widget> children;
  final Widget title;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      expansionAnimationStyle: AnimationStyle.noAnimation,
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      collapsedShape: const Border(),
      title: title,
      initiallyExpanded: initiallyExpanded,
      children: children,
    );
  }
}
