import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_result.dart';
import 'api.dart';

part 'test_results.g.dart';

@riverpod
Future<List<TestResult>> testResults(
  TestResultsRef ref,
  int testExecutionId,
) async {
  final api = ref.watch(apiProvider);
  return await api.getTestExecutionResults(testExecutionId);
}
