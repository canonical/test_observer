import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import 'dashboard/dashboard.dart';

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return YaruTheme(
      builder: (context, yaru, child) {
        return MaterialApp(
          theme: yaru.theme,
          darkTheme: yaru.darkTheme,
          home: const Dashboard(),
        );
      },
    );
  }
}
