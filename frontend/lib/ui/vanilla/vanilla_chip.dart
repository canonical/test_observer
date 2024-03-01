import 'package:flutter/material.dart';

class VanillaChip extends StatelessWidget {
  const VanillaChip({super.key, required this.text, this.fontColor});

  final String text;
  final Color? fontColor;

  @override
  Widget build(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    return Chip(
      label: Text(text, style: fontStyle?.apply(color: fontColor)),
      shape: const StadiumBorder(),
    );
  }
}
