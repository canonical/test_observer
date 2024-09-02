import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../providers/tests_issues.dart';

class TestIssuesPreloader extends ConsumerWidget {
  const TestIssuesPreloader({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(testsIssuesProvider);
    return child;
  }
}
