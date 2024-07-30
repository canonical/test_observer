import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import 'routing.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return YaruTheme(
      builder: (context, yaru, child) {
        final colorScheme = yaru.theme?.colorScheme.copyWith(
          surfaceContainerHigh: Colors.white, // search bars color
          surfaceContainerLow: Colors.white, // cards color
        );
        final theme = yaru.theme?.copyWith(colorScheme: colorScheme);

        return MaterialApp.router(
          theme: theme,
          routerConfig: appRouter,
        );
      },
    );
  }
}
