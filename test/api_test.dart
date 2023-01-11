import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/testcase_api/testcase_api_provider.dart';
import 'package:testcases/api.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  final container = ProviderContainer(overrides: [
    boardProvider('123').overrideWith((ref) => Future(() {
          print("Got here");
          return Board(id: "123", name: "foo", status: BoardStatusEnum.open);
        }))
  ]);

  test("Test accessing boards", () async {
    final board = container.read(boardProvider('123')).value;
    print('board');
    print(board);
    expect(board?.name, null);
  });
}
