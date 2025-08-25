import 'package:flutter/material.dart';

class NewTagChip extends StatelessWidget {
  const NewTagChip({super.key});

  @override
  Widget build(BuildContext context) {
    return Chip(
      label: Text(
        'NEW',
        style: const TextStyle(
          color: Colors.white,
          fontSize: 10,
          fontWeight: FontWeight.w600,
          letterSpacing: 0.5,
        ),
      ),
      backgroundColor: Colors.blue,
      visualDensity: VisualDensity(horizontal: -4, vertical: -4),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
      side: BorderSide.none,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
      ),
    );
  }
}
