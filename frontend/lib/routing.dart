// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
        GoRoute(
          path: AppRoutes.charms,
          pageBuilder: (_, __) => const NoTransitionPage(
            child: Dashboard(),
          ),
        ),
        GoRoute(
          path: '${AppRoutes.charms}/:artefactId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: ArtefactPage(
              artefactId: int.parse(state.pathParameters['artefactId']!),
            ),
          ),
        ),
        GoRoute(
          path: AppRoutes.images,
          pageBuilder: (_, __) => const NoTransitionPage(
            child: Dashboard(),
          ),
        ),
        GoRoute(
          path: '${AppRoutes.images}/:artefactId',
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

enum SortDirection {
  asc,
  desc,
}

class CommonQueryParameters {
  static const searchQuery = 'q';
  static const sortBy = 'sortBy';
  static const sortDirection = 'direction';
}

class AppRoutes {
  static const snaps = '/snaps';
  static const debs = '/debs';
  static const charms = '/charms';
  static const images = '/images';

  static Uri uriFromContext(BuildContext context) =>
      GoRouterState.of(context).uri;

  static FamilyName familyFromUri(Uri uri) {
    final path = uri.path;

    if (path.startsWith(snaps)) return FamilyName.snap;
    if (path.startsWith(debs)) return FamilyName.deb;
    if (path.startsWith(charms)) return FamilyName.charm;
    if (path.startsWith(images)) return FamilyName.image;

    throw Exception('Unknown route: $path');
  }

  static int artefactIdFromUri(Uri uri) {
    if (isArtefactPage(uri)) return uri.pathSegments[1].toInt();

    throw Exception('$uri isn\'t an artefact page');
  }

  static bool isDashboardPage(Uri uri) =>
      {snaps, debs, charms, images}.contains(uri.path);

  static bool isArtefactPage(Uri uri) =>
      (uri.path.contains(AppRoutes.snaps) ||
          uri.path.contains(AppRoutes.debs) ||
          uri.path.contains(AppRoutes.charms) ||
          uri.path.contains(AppRoutes.images)) &&
      uri.pathSegments.length == 2;

  static bool isIssuePage(Uri uri) =>
      uri.pathSegments.length == 2 && uri.pathSegments[0] == 'issues';

  static int issueIdFromUri(Uri uri) {
    if (isIssuePage(uri)) return int.parse(uri.pathSegments[1]);
    throw Exception('$uri isn\'t an issue page');
  }
}

void navigateToArtefactPage(BuildContext context, int artefactId) {
  final uri = AppRoutes.uriFromContext(context);
  final family = AppRoutes.familyFromUri(uri);
  String path = '/$artefactId';

  switch (family) {
    case FamilyName.deb:
      path = AppRoutes.debs + path;
      break;
    case FamilyName.snap:
      path = AppRoutes.snaps + path;
      break;
    case FamilyName.charm:
      path = AppRoutes.charms + path;
      break;
    case FamilyName.image:
      path = AppRoutes.images + path;
      break;
  }

  context.go(path);
}

void navigateToIssuePage(BuildContext context, int issueId) {
  context.go('/issues/$issueId');
}
