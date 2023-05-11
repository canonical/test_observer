import 'package:go_router/go_router.dart';

import 'dashboard/dashboard.dart';

final appRouter = GoRouter(
  initialLocation: '/snaps',
  routes: [
    GoRoute(
      path: '/',
      redirect: (context, state) => '/snaps',
    ),
    GoRoute(
      path: '/snaps',
      builder: (context, state) => const Dashboard(),
    ),
  ],
);
