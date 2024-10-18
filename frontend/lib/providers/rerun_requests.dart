import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/rerun_request.dart';
import 'api.dart';

part 'rerun_requests.g.dart';

@riverpod
class RerunRequests extends _$RerunRequests {
  @override
  Future<List<RerunRequest>> build() async {
    final api = ref.watch(apiProvider);
    return api.getRerunRequests();
  }

  void rerunTestExecutions(Set<int> testExecutionIds) async {
    final api = ref.read(apiProvider);
    final currentRerunRequests = await future;
    final addedRerunRequests = await api.rerunTestExecutions(testExecutionIds);
    state =
        AsyncData({...currentRerunRequests, ...addedRerunRequests}.toList());
  }
}
