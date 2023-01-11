import 'package:appflowy_board/appflowy_board.dart';
import 'package:flutter/material.dart';

final AppFlowyBoardController controller = AppFlowyBoardController(
  onMoveGroup: (fromGroupId, fromIndex, toGroupId, toIndex) {
    debugPrint('Move item from $fromIndex to $toIndex');
  },
  onMoveGroupItem: (groupId, fromIndex, toIndex) {
    debugPrint('Move $groupId:$fromIndex to $groupId:$toIndex');
  },
  onMoveGroupItemToGroup: (fromGroupId, fromIndex, toGroupId, toIndex) {
    debugPrint('Move $fromGroupId:$fromIndex to $toGroupId:$toIndex');
  },
);

class BoardContent extends StatefulWidget {
  const BoardContent({Key? key}) : super(key: key);

  @override
  State<BoardContent> createState() => _BoardContentState();
}

class TextItem extends AppFlowyGroupItem {
  final String s;
  TextItem(this.s);

  @override
  String get id => s;
}

class _BoardContentState extends State<BoardContent> {
  late AppFlowyBoardScrollController scrollManager;

  final config = const AppFlowyBoardConfig();

  @override
  void initState() {
    final group1 = AppFlowyGroupData(
        id: "To Do",
        items: [
          TextItem("Card 1"),
          TextItem("Card 2"),
        ],
        name: 'Group 1');
    final group2 = AppFlowyGroupData(
        id: "In Progress",
        items: [
          TextItem("Card 3"),
          TextItem("Card 4"),
        ],
        name: 'Group 2');

    final group3 = AppFlowyGroupData(id: "Done", items: [], name: "Group 3");

    controller.addGroup(group1);
    controller.addGroup(group2);
    controller.addGroup(group3);
    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    return AppFlowyBoard(
      controller: controller,
      cardBuilder: (context, group, groupItem) {
        final textItem = groupItem as TextItem;
        return AppFlowyGroupCard(
          key: ObjectKey(textItem),
          child: Text(textItem.s),
        );
      },
      groupConstraints: const BoxConstraints.tightFor(width: 240),
    );
  }
}
