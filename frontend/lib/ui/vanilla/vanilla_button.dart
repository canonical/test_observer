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
