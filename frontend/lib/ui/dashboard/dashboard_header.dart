import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../routing.dart';
import '../spacing.dart';

class DashboardHeader extends StatelessWidget {
  const DashboardHeader({Key? key, required this.title}) : super(key: key);

  final String title;

  @override
  Widget build(BuildContext context) {
    final uri = AppRoutes.uriFromContext(context);
    final queryParameters = uri.queryParameters;
    final viewMode = queryParameters['view'] == 'list' ? 'list' : 'dashboard';

    return Padding(
      padding: const EdgeInsets.only(
        top: Spacing.level5,
        bottom: Spacing.level4,
      ),
      child: Row(
        children: [
          Text(title, style: Theme.of(context).textTheme.headlineLarge),
          const Spacer(),
          ToggleButtons(
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
          ),
        ],
      ),
    );
  }
}
