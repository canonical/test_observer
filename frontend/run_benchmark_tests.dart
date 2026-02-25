// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'dart:convert' show JsonEncoder;
import 'dart:io';

import 'package:web_benchmarks/server.dart';

Future<void> main(List<String> args) async {
  final isHeadless = args.contains('--headless');

  await runBenchmarkRunnerFile(
    'benchmarks/artefact_page_tapping.dart',
    '#/snaps/0',
    isHeadless,
  );
  await runBenchmarkRunnerFile(
    'benchmarks/artefact_page_scrolling.dart',
    '#/snaps/0',
    isHeadless,
  );
}

Future<void> runBenchmarkRunnerFile(
  String file,
  String initialPage,
  bool isHeadless,
) async {
  final results = await serveWebBenchmark(
    benchmarkAppDirectory: Directory('.'),
    entryPoint: file,
    benchmarkPath: initialPage,
    headless: isHeadless,
  );

  final resultFile = File(
    file.replaceFirst('.dart', '_${formatDate(DateTime.now().toUtc())}.json'),
  );

  await resultFile.writeAsString(
    const JsonEncoder.withIndent('  ').convert(results.toJson()),
  );
}

String formatDate(DateTime date) {
  return '${date.year}-${date.month}-${date.day}_${date.hour}-${date.minute}-${date.second}';
}
