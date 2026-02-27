// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';

class BlinkingContent extends StatefulWidget {
  final Widget child;
  final bool blink;
  final int? numBlinks;

  const BlinkingContent({
    super.key,
    required this.child,
    required this.blink,
    this.numBlinks,
  });

  @override
  State<BlinkingContent> createState() => _BlinkingContentState();
}

class _BlinkingContentState extends State<BlinkingContent> {
  Color? _backgroundColor;

  @override
  void initState() {
    super.initState();
    _backgroundColor = null;
    if (widget.blink) {
      WidgetsBinding.instance.addPostFrameCallback((_) async {
        if (!mounted) return;
        final theme = Theme.of(context);
        final baseColor = theme.colorScheme.surface;
        final blinkColor = theme.brightness == Brightness.dark
            ? baseColor.withValues(alpha: 0.7)
            : Colors.grey.shade300;
        for (int i = 0; i < (widget.numBlinks ?? 3); i++) {
          if (!mounted) return;
          setState(() => _backgroundColor = blinkColor);
          await Future.delayed(const Duration(milliseconds: 120));
          if (!mounted) return;
          setState(() => _backgroundColor = null);
          await Future.delayed(const Duration(milliseconds: 120));
        }
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 120),
      color: _backgroundColor,
      child: widget.child,
    );
  }
}
