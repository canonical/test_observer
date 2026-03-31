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

/// Shows a notification SnackBar with the given [message].
/// Optionally, you can provide a [duration], [backgroundColor] and [textColor].
/// When [backgroundColor] is provided without [textColor], the text color will
/// be automatically determined using the theme's color scheme for proper contrast.
void showNotification(
  BuildContext context,
  String message, {
  Duration duration = const Duration(seconds: 3),
  Color? backgroundColor,
  Color? textColor,
}) {
  final theme = Theme.of(context);

  // Determine text color based on background using Material Design's color scheme
  final effectiveTextColor = textColor ??
      (backgroundColor != null
          ? _getOnColor(theme.colorScheme, backgroundColor)
          : null);

  final snackBar = SnackBar(
    behavior: SnackBarBehavior.floating,
    content: Text(
      message,
      style: effectiveTextColor != null
          ? TextStyle(color: effectiveTextColor)
          : null,
    ),
    duration: duration,
    width: 400,
    backgroundColor: backgroundColor,
  );
  ScaffoldMessenger.of(context).showSnackBar(snackBar);
}

/// Returns the appropriate "on" color from the color scheme for the given background,
/// following Material Design principles for accessible contrast.
Color _getOnColor(ColorScheme colorScheme, Color backgroundColor) {
  // Check if background matches theme colors and return corresponding "on" color
  if (backgroundColor == colorScheme.primary) {
    return colorScheme.onPrimary;
  } else if (backgroundColor == colorScheme.secondary) {
    return colorScheme.onSecondary;
  } else if (backgroundColor == colorScheme.error) {
    return colorScheme.onError;
  } else if (backgroundColor == colorScheme.surface) {
    return colorScheme.onSurface;
  }

  // For custom colors, use white or black based on luminance for reliable contrast
  final luminance = backgroundColor.computeLuminance();
  
  // Return white for dark backgrounds, black for light backgrounds
  // Threshold of 0.5 is a common heuristic for accessibility
  return luminance > 0.5 ? Colors.black : Colors.white;
}
