import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import 'dashboard/dashboard.dart';
import 'dashboard/navbar.dart';

final appRouter = GoRouter(
  initialLocation: navbarEntries[0].url,
  routes: [
    GoRoute(
      path: '/',
      redirect: (context, state) => navbarEntries[0].url,
    ),
    ShellRoute(
      builder: (_, __, ___) => const Dashboard(),
      routes: navbarEntries
          .map(
            (entry) => GoRoute(
              path: entry.url,
              builder: (_, __) => Container(),
            ),
          )
          .toList(),
    ),
  ],
);
