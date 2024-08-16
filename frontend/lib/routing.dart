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

class CommonQueryParameters {
  static const searchQuery = 'q';
}

class AppRoutes {
  static const snaps = '/snaps';
  static const debs = '/debs';

  static Uri uriFromContext(BuildContext context) =>
      GoRouterState.of(context).uri;

  static FamilyName familyFromUri(Uri uri) {
    final path = uri.path;

    if (path.startsWith(snaps)) return FamilyName.snap;
    if (path.startsWith(debs)) return FamilyName.deb;

    throw Exception('Unknown route: $path');
  }

  static int artefactIdFromUri(Uri uri) {
    if (isArtefactPage(uri)) return uri.pathSegments[1].toInt();

    throw Exception('$uri isn\'t an artefact page');
  }

  static bool isDashboardPage(Uri uri) => {snaps, debs}.contains(uri.path);

  static bool isArtefactPage(Uri uri) =>
      (uri.path.contains(AppRoutes.snaps) ||
          uri.path.contains(AppRoutes.debs)) &&
      uri.pathSegments.length == 2;
}
