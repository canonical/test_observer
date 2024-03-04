import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'models/family_name.dart';
import 'ui/artefact_page/artefact_page.dart';
import 'ui/dashboard/dashboard.dart';
import 'ui/dialog_page.dart';
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
          pageBuilder: (_, __) => const NoTransitionPage(
            child: Dashboard(),
          ),
        ),
        GoRoute(
          path: '${AppRoutes.snaps}/:artefactId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: ArtefactPage(
              artefactId: int.parse(state.pathParameters['artefactId']!),
            ),
          ),
        ),
        GoRoute(
          path: AppRoutes.debs,
          pageBuilder: (_, __) => const NoTransitionPage(
            child: Dashboard(),
          ),
        ),
        GoRoute(
          path: '${AppRoutes.debs}/:artefactId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: ArtefactPage(
              artefactId: int.parse(state.pathParameters['artefactId']!),
            ),
          ),
        ),
      ],
    ),
  ],
);

class AppRoutes {
  static const snaps = '/snaps';
  static const debs = '/debs';

  static FamilyName familyFromContext(BuildContext context) {
    final route = GoRouterState.of(context).fullPath!;

    if (route.startsWith(snaps)) {
      return FamilyName.snap;
    } else if (route.startsWith(debs)) {
      return FamilyName.deb;
    } else {
      throw Exception('Unknown route: $route');
    }
  }

  static int artefactIdFromContext(BuildContext context) {
    final Map<String, String> pathParameters =
        GoRouterState.of(context).pathParameters;

    if (!pathParameters.containsKey('artefactId')) {
      throw Exception('Artefact ID not found in path');
    }
    return int.parse(pathParameters['artefactId']!);
  }

  static bool isAtDashboardPage(BuildContext context) {
    final route = GoRouterState.of(context).fullPath!;
    return {snaps, debs}.contains(route);
  }
}
