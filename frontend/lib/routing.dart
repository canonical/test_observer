import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'models/family_name.dart';
import 'ui/artefact_dialog/artefact_dialog.dart';
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
          routes: [
            GoRoute(
              path: ':artefactId',
              pageBuilder: (context, state) => DialogPage(
                builder: (_) => ArtefactDialog(
                  artefactId: state.pathParameters['artefactId']!,
                ),
              ),
            ),
          ],
        ),
        GoRoute(
          path: AppRoutes.debs,
          pageBuilder: (_, __) => const NoTransitionPage(
            child: Dashboard(),
          ),
          routes: [
            GoRoute(
              path: ':artefactId',
              pageBuilder: (context, state) => DialogPage(
                builder: (_) => ArtefactDialog(
                  artefactId: state.pathParameters['artefactId']!,
                ),
              ),
            ),
          ],
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
}
