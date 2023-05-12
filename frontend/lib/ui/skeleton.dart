import 'package:flutter/material.dart';

import 'footer.dart';
import 'navbar.dart';

class Skeleton extends StatelessWidget {
  const Skeleton({super.key, required this.body});

  final Widget body;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          const Navbar(),
          Expanded(child: body),
        ],
      ),
      bottomNavigationBar: const Footer(),
    );
  }
}
