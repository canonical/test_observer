import 'package:flutter/material.dart';

import 'spacing.dart';

class Expandable extends StatelessWidget {
  const Expandable({
    super.key,
    required this.title,
    required this.children,
    this.initiallyExpanded = false,
  });

  final List<Widget> children;
  final Widget title;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      expansionAnimationStyle: AnimationStyle.noAnimation,
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      collapsedShape: const Border(),
      title: title,
      initiallyExpanded: initiallyExpanded,
      children: children,
    );
  }
}
