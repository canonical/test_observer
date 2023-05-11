import 'package:flutter/material.dart' hide Title;
import 'package:flutter_riverpod/flutter_riverpod.dart' hide Family;
import 'package:yaru_widgets/widgets.dart';

import '../providers/providers.dart';
import 'body/body.dart';
import 'footer.dart';
import 'title.dart';
import 'header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final families = ref.watch(fetchFamiliesProvider);

    return families.when(
      error: (error, _) => Text('Error: $error'),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
      data: (families) => Scaffold(
        body: Column(
          children: [
            Header(families: families),
            const Title(),
            const Expanded(child: Body()),
          ],
        ),
        bottomNavigationBar: const Footer(),
      ),
    );
  }
}
