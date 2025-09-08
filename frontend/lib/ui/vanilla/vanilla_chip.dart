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

class VanillaChip extends StatelessWidget {
  const VanillaChip({
    super.key,
    required this.text,
    this.fontColor,
    this.backgroundColor,
    this.side,
  });

  final String text;
  final Color? fontColor;
  final Color? backgroundColor;
  final BorderSide? side;

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    return Chip(
      label: Text(text, style: fontStyle?.apply(color: fontColor)),
      shape: const StadiumBorder(),
      backgroundColor: backgroundColor,
      side: side,
    );
  }
}
