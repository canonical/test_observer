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
    initialPage: initialPage,
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
