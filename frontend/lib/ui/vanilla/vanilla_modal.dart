// Copyright (C) 2023-2025 Canonical Ltd.
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

import 'vanilla_colors.dart';

class VanillaModal extends StatelessWidget {
  const VanillaModal({
    super.key,
    this.content,
    this.title,
    this.actions,
  });

  final Widget? title;
  final Widget? content;
  final List<Widget>? actions;

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      backgroundColor: VanillaColors.backgroundDefault,
      shape: const RoundedRectangleBorder(),
      title: title,
      content: content,
      actions: actions,
    );
  }
}

Future<T?> showVanillaModal<T>({
  required BuildContext context,
  required Widget Function(BuildContext) builder,
}) {
  return showDialog(
    barrierColor: VanillaColors.backgroundOverlay,
    context: context,
    builder: builder,
  );
}
