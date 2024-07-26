import 'package:flutter/material.dart';

import 'view_mode_manager.dart';

class ViewModeToggle extends StatelessWidget {
  const ViewModeToggle({super.key});

  @override
  Widget build(BuildContext context) {
    final viewModeManager = ViewModeManager(context);
    final currentViewMode = viewModeManager.currentViewMode();

    return ToggleButtons(
      isSelected: [
        currentViewMode == ViewMode.list,
        currentViewMode == ViewMode.dashboard,
      ],
      children: const [Icon(Icons.list), Icon(Icons.dashboard)],
      onPressed: (i) {
        final selectedView = [ViewMode.list, ViewMode.dashboard][i];
        ViewModeManager(context).switchView(selectedView);
      },
    );
  }
}
