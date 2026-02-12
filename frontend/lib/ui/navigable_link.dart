// Copyright (C) 2026 Canonical Ltd.
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
import 'package:flutter/gestures.dart';
import 'package:flutter/services.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

/// A widget that provides consistent navigation behavior with accessibility support.
///
/// Handles:
/// - Regular tap/click navigation
/// - Middle-click to open in new tab
/// - Ctrl/Cmd+Click to open in new tab
/// - Keyboard navigation (Enter/Space)
/// - Screen reader support with link semantics
///
/// Use either [path] for in-app navigation or [onNavigate]/[onOpenInNewTab] for custom behavior.
class NavigableLink extends StatelessWidget {
  const NavigableLink({
    super.key,
    required this.child,
    this.path,
    this.onNavigate,
    this.onOpenInNewTab,
    this.tooltip,
    this.semanticsLabel,
  }) : assert(
          path != null || onNavigate != null,
          'Either path or onNavigate must be provided',
        );

  /// The widget to display
  final Widget child;

  /// In-app navigation path. If provided, handles both regular navigation
  /// (via context.go) and opening in a new tab automatically.
  final String? path;

  /// Called when the user performs a regular navigation action
  /// (tap, Enter key, or Space key). Overrides [path] if provided.
  final VoidCallback? onNavigate;

  /// Called when the user requests to open in a new tab
  /// (middle-click or Ctrl/Cmd+Click).
  /// If null but [path] is provided, will open path in new tab.
  final VoidCallback? onOpenInNewTab;

  /// Optional tooltip to display on hover
  final String? tooltip;

  /// Optional label for screen readers. If not provided,
  /// a default "Navigate" label is used.
  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    // Determine callbacks based on path or custom callbacks
    final navigateCallback =
        onNavigate ?? (path != null ? () => context.go(path!) : () {});
    final openInNewTabCallback = onOpenInNewTab ??
        (path != null
            ? () => launchUrl(
                  Uri.base.replace(fragment: path!),
                  mode: LaunchMode.externalApplication,
                )
            : null);

    Widget result = Listener(
      onPointerDown: openInNewTabCallback != null
          ? (PointerDownEvent event) {
              // Middle mouse button opens in new tab
              if (event.buttons & kMiddleMouseButton != 0) {
                openInNewTabCallback();
              }
            }
          : null,
      child: Focus(
        onKeyEvent: (FocusNode node, KeyEvent event) {
          if (event is KeyDownEvent && openInNewTabCallback != null) {
            // Ctrl/Cmd + Enter/Space opens in new tab (keyboard navigation)
            final isModifierPressed =
                HardwareKeyboard.instance.isControlPressed ||
                    HardwareKeyboard.instance.isMetaPressed;
            if (isModifierPressed &&
                (event.logicalKey == LogicalKeyboardKey.enter ||
                    event.logicalKey == LogicalKeyboardKey.space)) {
              openInNewTabCallback();
              return KeyEventResult.handled;
            }
          }
          return KeyEventResult.ignored;
        },
        child: MouseRegion(
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            onTap: () {
              // Check for Ctrl/Cmd at tap time
              if (openInNewTabCallback != null) {
                final isControlPressed =
                    HardwareKeyboard.instance.isControlPressed ||
                        HardwareKeyboard.instance.isMetaPressed;
                if (isControlPressed) {
                  openInNewTabCallback();
                  return;
                }
              }
              // Normal navigation
              navigateCallback();
            },
            child: child,
          ),
        ),
      ),
    );

    // Add semantics for screen readers
    result = Semantics(
      link: true,
      label: semanticsLabel ?? 'Navigate',
      onTap: navigateCallback,
      child: result,
    );

    // Add tooltip if provided
    if (tooltip != null) {
      result = Tooltip(
        message: tooltip!,
        child: result,
      );
    }

    return result;
  }
}

/// Helper to create a navigable link that opens URLs in the current or new tab.
///
/// This is specifically for URL-based navigation (using url_launcher).
class UrlNavigableLink extends StatelessWidget {
  const UrlNavigableLink({
    super.key,
    required this.child,
    required this.url,
    this.tooltip,
    this.semanticsLabel,
  });

  final Widget child;
  final Uri url;
  final String? tooltip;
  final String? semanticsLabel;

  @override
  Widget build(BuildContext context) {
    return NavigableLink(
      onNavigate: () => launchUrl(url),
      onOpenInNewTab: () => launchUrl(
        url,
        mode: LaunchMode.externalApplication,
      ),
      tooltip: tooltip,
      semanticsLabel: semanticsLabel,
      child: child,
    );
  }
}
