import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart' hide Family;

import '../models/family.dart';
import 'body/body.dart';
import 'footer.dart';
import 'header.dart';
import 'navbar.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Column(
        children: const [
          Navbar(),
          Header(),
          Expanded(child: Body(family: dummyFamily)),
        ],
      ),
      bottomNavigationBar: const Footer(),
    );
  }
}
