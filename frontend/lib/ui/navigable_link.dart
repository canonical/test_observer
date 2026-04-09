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
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/link.dart';
import 'package:url_launcher/url_launcher.dart';

/// A widget that provides consistent navigation behavior with accessibility support.
///
/// Wraps its child in an HTML [Link] (<a> tag) so the browser handles
/// middle-click and Ctrl/Cmd+Click to open in a new tab natively.
/// Regular clicks navigate in-app via [context.go].
class NavigableLink extends StatelessWidget {
  const NavigableLink({
    super.key,
    required this.child,
    required this.path,
    this.tooltip,
    this.semanticsLabel,
  });

  /// The widget to display.
  final Widget child;

  /// In-app navigation path. Used for both regular navigation (context.go)
  /// and as the href of the rendered <a> tag.
  final String path;

  /// Optional tooltip to display on hover.
  final String? tooltip;

  /// Optional label for screen readers. Defaults to "Navigate".
  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    final uri = Uri.base.replace(fragment: path);

    Widget result = Link(
      uri: uri,
      builder: (context, followLink) => MouseRegion(
        cursor: SystemMouseCursors.click,
        child: InkWell(
          onTap: followLink == null
              ? null
              : () {
                  if (HardwareKeyboard.instance.isControlPressed ||
                      HardwareKeyboard.instance.isMetaPressed) {
                    launchUrl(uri, mode: LaunchMode.externalApplication);
                    return;
                  }
                  context.go(path);
                },
          child: child,
        ),
      ),
    );

    result = Semantics(
      link: true,
      label: semanticsLabel ?? 'Navigate',
      onTap: () => context.go(path),
      child: result,
    );

    if (tooltip != null) {
      result = Tooltip(
        message: tooltip!,
        child: result,
      );
    }

    return result;
  }
}
