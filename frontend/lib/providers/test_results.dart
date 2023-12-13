import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_result.dart';
import 'dio.dart';

part 'test_results.g.dart';

@riverpod
Future<List<TestResult>> testResults(
  TestResultsRef ref,
  int testExecutionId,
) async {
  final dio = ref.watch(dioProvider);

  final response =
      await dio.get('/v1/test-executions/$testExecutionId/test-results');
  final List testResultsJson = response.data;
  final testResults =
      testResultsJson.map((json) => TestResult.fromJson(json)).toList();
  return testResults;
}
