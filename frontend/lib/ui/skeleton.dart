import 'package:flutter/material.dart';

import 'dashboard/find_shortcut.dart';
import 'footer.dart';
import 'navbar.dart';

class Skeleton extends StatelessWidget {
  const Skeleton({super.key, required this.body});

  final Widget body;

  @override
  Widget build(BuildContext context) {
    return FindShortcut(
      child: SelectionArea(
        child: Scaffold(
          body: Column(
            children: [
              const Navbar(),
              Expanded(child: body),
            ],
          ),
          bottomNavigationBar: const Footer(),
        ),
      ),
    );
  }
}
