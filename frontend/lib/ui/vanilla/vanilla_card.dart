import 'package:flutter/material.dart';

import 'vanilla_colors.dart';

class VanillaCard extends StatelessWidget {
  const VanillaCard({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(0),
      elevation: 0,
      color: VanillaColors.backgroundDefault,
      shape: const RoundedRectangleBorder(
        side: BorderSide(color: VanillaColors.borderDefault, width: 1.5),
      ),
      child: child,
    );
  }
}
