// Copyright (C) 2023-2025 Canonical Ltd.
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
