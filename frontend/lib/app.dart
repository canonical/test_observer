import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import 'dashboard/dashboard.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return ProviderScope(
      child: YaruTheme(
        builder: (context, yaru, child) {
          return MaterialApp(
            theme: yaru.theme,
            // Colors are fixed as design doesn't support dark theme
            darkTheme: yaru.theme,
            home: const Dashboard(),
          );
        },
      ),
    );
  }
}
