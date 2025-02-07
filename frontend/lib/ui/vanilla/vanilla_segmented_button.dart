import 'package:flutter/material.dart';

import 'vanilla_colors.dart';

class VanillaSegmentedButton extends StatelessWidget {
  const VanillaSegmentedButton(
      {super.key,
      required this.segments,
      required this.selected,
      this.onSelectionChanged});

  final List<ButtonSegment> segments;
  final Set<dynamic> selected;
  final Function(Set<dynamic>)? onSelectionChanged;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton(
      selectedIcon: const SizedBox.shrink(),
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
      segments: segments,
      selected: selected,
      onSelectionChanged: onSelectionChanged,
    );
  }
}
