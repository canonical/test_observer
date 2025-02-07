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

class VanillaButton extends StatelessWidget {
  const VanillaButton({
    super.key,
    this.onPressed,
    this.child,
    this.type = VanillaButtonType.normal,
    this.autofocus = false,
  });

  final void Function()? onPressed;
  final Widget? child;
  final VanillaButtonType type;
  final bool autofocus;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      autofocus: autofocus,
      onPressed: onPressed,
      style: ButtonStyle(
        foregroundColor: WidgetStatePropertyAll(type.textColor),
        overlayColor: const WidgetStatePropertyAll(Colors.transparent),
        backgroundColor: WidgetStateProperty.resolveWith<Color?>(
          (Set<WidgetState> states) {
            if (states.contains(WidgetState.hovered)) {
              return type.backgroundHoverColor;
            }
            return type.backgroundColor;
          },
        ),
        shape: const WidgetStatePropertyAll(RoundedRectangleBorder()),
        side: WidgetStatePropertyAll(
          BorderSide(color: type.borderColor, width: 1),
        ),
      ),
      child: child,
    );
  }
}

enum VanillaButtonType {
  normal,
  positive,
  negative;

  Color get backgroundColor {
    switch (this) {
      case normal:
        return VanillaColors.backgroundDefault;
      case positive:
        return VanillaColors.basePositive;
      case negative:
        return VanillaColors.baseNegative;
    }
  }

  Color get textColor {
    switch (this) {
      case normal:
        return VanillaColors.textDefault;
      case positive:
        return VanillaColors.textButtonPositive;
      case negative:
        return VanillaColors.textButtonNegative;
    }
  }

  Color get borderColor {
    switch (this) {
      case normal:
        return VanillaColors.borderHighContrast;
      case positive:
        return VanillaColors.basePositive;
      case negative:
        return VanillaColors.baseNegative;
    }
  }

  Color get backgroundHoverColor {
    switch (this) {
      case normal:
        return VanillaColors.backgroundHover;
      case positive:
        return VanillaColors.buttonPositiveHover;
      case negative:
        return VanillaColors.buttonNegativeHover;
    }
  }
}
