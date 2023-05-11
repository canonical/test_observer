import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:yaru/yaru.dart';

import 'dashboard/dashboard.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      child: YaruTheme(
        builder: (context, yaru, child) {
          return MaterialApp.router(
            theme: yaru.theme,
            // Colors are fixed as design doesn't support dark theme
            darkTheme: yaru.theme,
            routerConfig: GoRouter(
              initialLocation: '/snaps',
              routes: [
                GoRoute(
                  path: '/',
                  redirect: (context, state) => '/snaps',
                ),
                ShellRoute(
                  builder: (_, __, ___) => const Dashboard(),
                  routes: [
                    GoRoute(
                      path: '/snaps',
                      builder: (_, __) => Container(),
                    ),
                  ],
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
