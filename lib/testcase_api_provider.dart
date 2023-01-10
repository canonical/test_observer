import 'package:riverpod/riverpod.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:testcases/api.dart';

final clientProvider = Provider<ApiClient>((ref) => ApiClient());

// ignore: unused_element
final _fixedBoardProvider = FutureProvider((ref) async {
  return Board(id: "foo", name: 'bar', status: BoardStatusEnum.open);
});

// ignore: unused_element
final _boardByFixedIdProvider = FutureProvider((ref) async {
  final boardApi = BoardApi(ref.watch(clientProvider));
  return boardApi.getBoardById('foo');
});

final boardProvider = FutureProviderFamily<Board?, String>((ref, id) async {
  final boardApi = BoardApi(ref.watch(clientProvider));
  return boardApi.getBoardById(id);
});
