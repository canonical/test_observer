import 'package:flutter/material.dart';

import 'vanilla_colors.dart';

class VanillaCheckbox extends StatelessWidget {
  const VanillaCheckbox({super.key, this.value, this.onChanged});

  final bool? value;
  final void Function(bool?)? onChanged;

  @override
  Widget build(BuildContext context) {
    return Checkbox(
      splashRadius: 0,
      fillColor: WidgetStateProperty.resolveWith<Color?>(
        (Set<WidgetState> states) {
          if (states.contains(WidgetState.selected)) {
            return VanillaColors.backgroundCheckboxChecked;
          }
          if (states.contains(WidgetState.hovered)) {
            return VanillaColors.backgroundHover;
          }
          return VanillaColors.backgroundDefault;
        },
      ),
      shape: const RoundedRectangleBorder(),
      side: const BorderSide(
        color: VanillaColors.borderHighContrast,
        width: 1,
      ),
      value: value,
      onChanged: onChanged,
    );
  }
}
