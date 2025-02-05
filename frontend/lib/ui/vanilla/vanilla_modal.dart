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
