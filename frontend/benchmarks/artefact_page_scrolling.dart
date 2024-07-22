import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:web_benchmarks/client.dart';

import 'common.dart';

class ScrollRecorder extends AppRecorder {
  ScrollRecorder() : super(benchmarkName: 'scrolling');

  @override
  Future<void> start() async {
    final firstTestExecution = find.text('Environment 0').evaluate().first;
    final scrollable = Scrollable.of(firstTestExecution);

    while (true) {
      await scrollable.position.animateTo(
        scrollable.position.maxScrollExtent,
        curve: Curves.linear,
        duration: const Duration(seconds: 10),
      );
      await scrollable.position.animateTo(
        scrollable.position.minScrollExtent,
        curve: Curves.linear,
        duration: const Duration(seconds: 10),
      );
    }
  }
}

Future<void> main() async {
  await runBenchmarks(
    <String, RecorderFactory>{
      'scrolling': () => ScrollRecorder(),
    },
  );
}
