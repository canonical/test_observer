import 'package:flutter/material.dart';

import 'body/body.dart';
import 'footer.dart';
import 'header.dart';
import 'navbar.dart';

class Dashboard extends StatelessWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: const [
          Navbar(),
          Header(),
          Expanded(child: Body()),
        ],
      ),
      bottomNavigationBar: const Footer(),
    );
  }
}
