// Copyright (C) 2024 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

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
