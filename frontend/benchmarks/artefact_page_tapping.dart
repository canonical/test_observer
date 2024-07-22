import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:web_benchmarks/client.dart';

import 'common.dart';

class TapRecorder extends AppRecorder {
  TapRecorder() : super(benchmarkName: 'tapping');

  @override
  Future<void> start() async {
    final controller = LiveWidgetController(WidgetsBinding.instance);
    final firstTestExecution = find.text('Environment 0');
    final failedSection = find.textContaining(RegExp(r'Failed \d+'));
    final passedSection = find.textContaining(RegExp(r'Passed \d+'));
    final skippedSection = find.textContaining(RegExp(r'Skipped \d+'));

    while (true) {
      await controller.tap(firstTestExecution);
      await controller.pumpAndSettle();
      await controller.tap(failedSection);
      await controller.pumpAndSettle();
      await controller.tap(skippedSection);
      await controller.pumpAndSettle();
      await controller.tap(passedSection);
      await controller.pumpAndSettle();
      await controller.tap(firstTestExecution);
      await controller.pumpAndSettle();
    }
  }
}

Future<void> main() async {
  await runBenchmarks(
    <String, RecorderFactory>{
      'tapping': () => TapRecorder(),
    },
  );
}
