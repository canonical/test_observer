// Copyright 2023 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2023 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'models/family_name.dart';
import 'frontend_config.dart';
import 'ui/artefact_page/artefact_page.dart';
import 'ui/dashboard/dashboard.dart';
import 'ui/issues_page/issues_page.dart';
import 'ui/skeleton.dart';
import 'ui/test_results_page/test_results_page.dart';
import 'ui/issue_page/issue_page.dart';

final appRouter = GoRouter(
  routes: [
    GoRoute(path: '/', redirect: (context, state) => configuredTabs.first),
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
        GoRoute(
          path: AppRoutes.testResults,
          pageBuilder: (_, __) => const NoTransitionPage(
            child: TestResultsPage(),
          ),
        ),
        GoRoute(
          path: '/issues',
          pageBuilder: (_, __) => const NoTransitionPage(
            child: IssuesPage(),
          ),
        ),
        GoRoute(
          path: '/issues/:issueId',
          pageBuilder: (context, state) => NoTransitionPage(
            child: IssuePage(
              issueId: int.parse(state.pathParameters['issueId']!),
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
  static const attachmentRule = 'attachmentRule';
}

class AppRoutes {
  static const snaps = '/snaps';
  static const debs = '/debs';
  static const charms = '/charms';
  static const images = '/images';
  static const testResults = '/test-results';

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

  static bool isTestResultsPage(Uri uri) => uri.path == testResults;

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

  static bool isIssuesPage(Uri uri) => uri.path == '/issues';
}

String getArtefactPagePathForFamily(
  FamilyName family,
  int artefactId, {
  int? testExecutionId,
  int? testResultId,
}) {
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

  if (testExecutionId != null || testResultId != null) {
    final queryParams = <String, String>{};
    if (testExecutionId != null) {
      queryParams['testExecutionId'] = testExecutionId.toString();
    }
    if (testResultId != null) {
      queryParams['testResultId'] = testResultId.toString();
    }
    final uri = Uri(path: path, queryParameters: queryParams);
    path = uri.toString();
  }

  return path;
}

String getArtefactPagePath(
  BuildContext context,
  int artefactId, {
  int? testExecutionId,
  int? testResultId,
}) {
  final uri = AppRoutes.uriFromContext(context);
  final family = AppRoutes.familyFromUri(uri);
  return getArtefactPagePathForFamily(
    family,
    artefactId,
    testExecutionId: testExecutionId,
    testResultId: testResultId,
  );
}

void navigateToArtefactPage(
  BuildContext context,
  int artefactId, {
  int? testExecutionId,
  int? testResultId,
}) {
  final path = getArtefactPagePath(
    context,
    artefactId,
    testExecutionId: testExecutionId,
    testResultId: testResultId,
  );
  context.go(path);
}

void navigateToIssuePage(
  BuildContext context,
  int issueId, {
  int? attachmentRuleId,
}) {
  final path = attachmentRuleId != null
      ? Uri(
          path: '/issues/$issueId',
          queryParameters: {
            CommonQueryParameters.attachmentRule: attachmentRuleId.toString(),
          },
        ).toString()
      : '/issues/$issueId';
  context.go(path);
}
