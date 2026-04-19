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

import 'package:flutter/material.dart';

import 'spacing.dart';

class SliverExpandable extends StatefulWidget {
  const SliverExpandable({
    super.key,
    required this.title,
    required this.sliverChildren,
    this.initiallyExpanded = false,
    this.tilePadding,
    this.childrenPadding = const EdgeInsets.only(left: Spacing.level4),
  });

  final List<Widget> sliverChildren;
  final Widget title;
  final bool initiallyExpanded;
  final EdgeInsetsGeometry? tilePadding;
  final EdgeInsetsGeometry childrenPadding;

  @override
  State<SliverExpandable> createState() => _SliverExpandableState();
}

class _SliverExpandableState extends State<SliverExpandable> {
  late bool _isExpanded;

  @override
  void initState() {
    super.initState();
    _isExpanded = widget.initiallyExpanded;
  }

  void _handleTap() {
    setState(() {
      _isExpanded = !_isExpanded;
    });
  }

  @override
  Widget build(BuildContext context) {
    return SliverMainAxisGroup(
      slivers: [
        SliverToBoxAdapter(
          child: ListTile(
            onTap: _handleTap,
            contentPadding: widget.tilePadding,
            leading:
                Icon(_isExpanded ? Icons.expand_more : Icons.chevron_right),
            title: widget.title,
          ),
        ),
        if (_isExpanded)
          SliverPadding(
            padding: widget.childrenPadding,
            sliver: SliverMainAxisGroup(
              slivers: widget.sliverChildren,
            ),
          ),
      ],
    );
  }
}
