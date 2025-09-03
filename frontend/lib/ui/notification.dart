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

/// Shows a notification SnackBar with the given [message].
/// Optionally, you can provide a [duration] and [backgroundColor].
void showNotification(
  BuildContext context,
  String message, {
  Duration duration = const Duration(seconds: 3),
  Color? backgroundColor,
  Color? textColor,
}) {
  final snackBar = SnackBar(
    behavior: SnackBarBehavior.floating,
    content: Text(message, style: TextStyle(color: textColor)),
    duration: duration,
    width: 400,
    backgroundColor: backgroundColor ?? Colors.green,
  );
  ScaffoldMessenger.of(context).showSnackBar(snackBar);
}
