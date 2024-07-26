import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../routing.dart';

class ViewTypeToggle extends StatelessWidget {
  const ViewTypeToggle({super.key});

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    final queryParameters = uri.queryParameters;
    final viewMode = queryParameters['view'] == 'list' ? 'list' : 'dashboard';

    return ToggleButtons(
      isSelected: [viewMode == 'list', viewMode == 'dashboard'],
      children: const [Icon(Icons.list), Icon(Icons.dashboard)],
      onPressed: (i) {
        final selectedView = ['list', 'dashboard'][i];
        context.go(
          uri.replace(
            queryParameters: {...queryParameters, 'view': selectedView},
          ).toString(),
        );
      },
    );
  }
}
