import 'package:go_router/go_router.dart';

import 'ui/dashboard.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      redirect: (context, state) => AppRoutes.snaps,
    ),
    GoRoute(
      path: AppRoutes.snaps,
      builder: (context, state) => const SnapDashboard(),
    ),
  ],
);

class AppRoutes {
  static const snaps = '/snaps';
}
