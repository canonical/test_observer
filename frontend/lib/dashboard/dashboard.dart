import 'package:flutter/material.dart' hide Title;
import 'package:flutter_riverpod/flutter_riverpod.dart' hide Family;

import 'body/body.dart';
import 'footer.dart';
import 'title.dart';
import 'header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      body: Column(
        children: const [
          Header(),
          Title(),
          Expanded(child: Body()),
        ],
      ),
      bottomNavigationBar: const Footer(),
    );
  }
}
