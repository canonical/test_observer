import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import 'routing.dart';
import 'ui/dashboard/find_shortcut.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return YaruTheme(
      builder: (context, yaru, child) {
        return FindShortcut(
          child: MaterialApp.router(
            theme: yaru.theme,
            // Colors are fixed as design doesn't support dark theme
            darkTheme: yaru.theme,
            routerConfig: appRouter,
          ),
        );
      },
    );
  }
}
