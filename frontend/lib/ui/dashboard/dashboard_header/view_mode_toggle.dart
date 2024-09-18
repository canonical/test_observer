import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../models/view_modes.dart';
import '../../../providers/view_mode.dart';

class ViewModeToggle extends ConsumerWidget {
  const ViewModeToggle({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final viewMode = ref.watch(viewModeProvider).value;

    if (viewMode == null) return const SizedBox.shrink();

    return ToggleButtons(
      isSelected: [
        viewMode == ViewModes.list,
        viewMode == ViewModes.dashboard,
      ],
      children: const [Icon(Icons.list), Icon(Icons.dashboard)],
      onPressed: (i) {
        final selectedView = [ViewModes.list, ViewModes.dashboard][i];
        ref.watch(viewModeProvider.notifier).set(selectedView);
      },
    );
  }
}
