import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_event.dart';
import 'api.dart';

part 'test_events.g.dart';

@riverpod
Future<List<TestEvent>> testEvents(
  TestEventsRef ref,
  int testExecutionId,
) async {
  final api = ref.watch(apiProvider);
  return await api.getTestExecutionEvents(testExecutionId);
}
