import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../routing.dart';
import '../spacing.dart';
import 'dashboard_body.dart';
import 'dashboard_header.dart';

class Dashboard extends ConsumerWidget {
  const Dashboard({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromContext(context);

    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            // Stretch header to be same size as body
            width: DashboardBody.getWidthForFamily(family),
            child: DashboardHeader(
              title: '${family.name.capitalize()} Update Verification',
            ),
          ),
          const Expanded(child: DashboardBody()),
        ],
      ),
    );
  }
}
