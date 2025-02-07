import 'package:flutter/material.dart';

import 'vanilla_colors.dart';

class VanillaIconButton extends StatelessWidget {
  const VanillaIconButton({super.key, required this.icon, this.onPressed});

  final Widget icon;
  final void Function()? onPressed;

  @override
  Widget build(BuildContext context) {
    return IconButton(
      style: ButtonStyle(
        foregroundColor:
            const WidgetStatePropertyAll(VanillaColors.textDefault),
        overlayColor: const WidgetStatePropertyAll(Colors.transparent),
        backgroundColor: WidgetStateProperty.resolveWith<Color?>(
          (Set<WidgetState> states) {
            if (states.contains(WidgetState.selected)) {
              return VanillaColors.backgroundActive;
            }
            if (states.contains(WidgetState.hovered)) {
              return VanillaColors.backgroundHover;
            }
            return VanillaColors.backgroundDefault;
          },
        ),
        shape: const WidgetStatePropertyAll(RoundedRectangleBorder()),
        side: const WidgetStatePropertyAll(
          BorderSide(
            color: VanillaColors.borderHighContrast,
            width: 1,
          ),
        ),
      ),
      icon: icon,
      onPressed: onPressed,
    );
  }
}
