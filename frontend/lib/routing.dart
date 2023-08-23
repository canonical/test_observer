import 'package:go_router/go_router.dart';

import 'ui/dashboard/dashboard.dart';
import 'ui/skeleton.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      redirect: (context, state) => AppRoutes.snaps,
    ),
    ShellRoute(
      builder: (_, __, dashboard) => Skeleton(
        body: dashboard,
      ),
      routes: [
        GoRoute(
          path: AppRoutes.snaps,
          pageBuilder: (_, __) =>
              const NoTransitionPage(child: SnapDashboard()),
        ),
        GoRoute(
          path: AppRoutes.debs,
          pageBuilder: (_, __) => const NoTransitionPage(child: DebDashboard()),
        ),
      ],
    ),
  ],
);

class AppRoutes {
  static const snaps = '/snaps';
  static const debs = '/debs';
}
