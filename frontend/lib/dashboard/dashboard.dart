import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/widgets.dart';

import '../providers.dart';
import 'body/body.dart';
import 'footer.dart';
import 'header.dart';
import 'navbar.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = ref.watch(fetchFamilyProvider('snaps'));

    return family.when(
      error: (error, _) => Text('Error: $error'),
      loading: () => const Center(
        child: YaruCircularProgressIndicator(),
      ),
      data: (family) => Scaffold(
        body: Column(
          children: [
            const Navbar(),
            Header(family: family),
            Expanded(child: Body(family: family)),
          ],
        ),
        bottomNavigationBar: const Footer(),
      ),
    );
  }
}
