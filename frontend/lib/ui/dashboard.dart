import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/widgets.dart';

import '../providers/fetch_stages.dart';
import 'body/body.dart';
import 'footer.dart';
import 'header.dart';
import 'navbar.dart';

class SnapDashboard extends StatelessWidget {
  const SnapDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return const Dashboard(
      familyName: 'snap',
      title: 'Snap Update Verification',
    );
  }
}

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key, required this.familyName, required this.title})
      : super(key: key);

  final String familyName;
  final String title;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stages = ref.watch(fetchStagesProvider(familyName));

    return stages.when(
      error: (error, _) => Text('Error: $error'),
      loading: () => const Center(
        child: YaruCircularProgressIndicator(),
      ),
      data: (stages) => Scaffold(
        body: Column(
          children: [
            const Navbar(),
            Header(title: title),
            Expanded(child: Body(stages: stages)),
          ],
        ),
        bottomNavigationBar: const Footer(),
      ),
    );
  }
}
