import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../providers/fetch_stages.dart';
import 'dashboard_body.dart';
import 'dashboard_header.dart';

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

    return Column(
      children: [
        DashboardHeader(title: title),
        Expanded(
          child: stages.when(
            error: (error, _) => Center(child: Text('Error: $error')),
            loading: () => const Center(child: YaruCircularProgressIndicator()),
            data: (stages) => DashboardBody(stages: stages),
          ),
        ),
      ],
    );
  }
}
