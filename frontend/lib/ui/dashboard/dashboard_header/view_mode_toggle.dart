import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../providers/view_mode.dart';

class ViewModeToggle extends ConsumerWidget {
  const ViewModeToggle({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final viewMode = ref.watch(viewModeProvider);

    return viewMode.when(
      loading: () => const SizedBox.shrink(),
      error: (_, __) => const SizedBox.shrink(),
      data: (viewMode) => ToggleButtons(
        isSelected: [
          viewMode == ViewModes.list,
          viewMode == ViewModes.dashboard,
        ],
        children: const [Icon(Icons.list), Icon(Icons.dashboard)],
        onPressed: (i) {
          final selectedView = [ViewModes.list, ViewModes.dashboard][i];
          ref.watch(viewModeProvider.notifier).set(selectedView);
        },
      ),
    );
  }
}
