import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../routing.dart';
import 'dashboard_body.dart';
import 'dashboard_header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final familyName = AppRoutes.familyFromContext(context);

    return Column(
      children: [
        DashboardHeader(
          title: '${familyName.name.capitalize()} Update Verification',
        ),
        const Expanded(child: DashboardBody()),
      ],
    );
  }
}
