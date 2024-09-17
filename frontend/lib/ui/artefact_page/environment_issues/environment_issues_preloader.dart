import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../providers/environments_issues.dart';

class EnvironmentIssuesPreloader extends ConsumerWidget {
  const EnvironmentIssuesPreloader({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(environmentsIssuesProvider);
    return child;
  }
}
