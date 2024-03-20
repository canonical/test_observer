import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'models/family_name.dart';
import 'ui/artefact_page/artefact_page.dart';
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

  static Uri uriFromContext(BuildContext context) =>
      GoRouterState.of(context).uri;

  static FamilyName familyFromUri(Uri uri) {
    final path = uri.path;

    if (path.startsWith(snaps)) {
      return FamilyName.snap;
    } else if (path.startsWith(debs)) {
      return FamilyName.deb;
    } else {
      throw Exception('Unknown route: $path');
    }
  }

  static int artefactIdFromUri(Uri uri) {
    final pathStartsWithFamily = uri.path.contains(AppRoutes.snaps) ||
        uri.path.contains(AppRoutes.snaps);
    if (pathStartsWithFamily && uri.pathSegments.length >= 2) {
      return uri.pathSegments[1].toInt();
    } else {
      throw Exception('No artefact id in route $uri');
    }
  }

  static bool isAtDashboardPage(BuildContext context) {
    final route = GoRouterState.of(context).fullPath!;
    return {snaps, debs}.contains(route);
  }
}
