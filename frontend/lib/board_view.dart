import 'package:appflowy_board/appflowy_board.dart';
import 'package:flutter/material.dart';

import 'build_artefact_card.dart';

class BoardView extends StatefulWidget {
  const BoardView({Key? key}) : super(key: key);

  @override
  State<BoardView> createState() => _BoardViewState();
}

class _BoardViewState extends State<BoardView> {
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

  late AppFlowyBoardScrollController boardController;

  @override
  void initState() {
    boardController = AppFlowyBoardScrollController();
    final group1 = AppFlowyGroupData(id: "Edge", name: "Edge", items: [
      BuildArtefactItem(observedCount: 5),
      BuildArtefactItem(),
      BuildArtefactItem(observedCount: 29),
      BuildArtefactItem(observedCount: 15),
      BuildArtefactItem(observedCount: 10),
      BuildArtefactItem(observedCount: 10),
    ]);

    final group2 = AppFlowyGroupData(
      id: "Beta",
      name: "Beta",
      items: <AppFlowyGroupItem>[
        BuildArtefactItem(observedCount: 12),
        BuildArtefactItem(observedCount: 1),
        BuildArtefactItem(),
        BuildArtefactItem(),
        BuildArtefactItem(),
      ],
    );

    final group3 = AppFlowyGroupData(
        id: "Candidate", name: "Candidate", items: <AppFlowyGroupItem>[]);

    controller.addGroup(group1);
    controller.addGroup(group2);
    controller.addGroup(group3);

    super.initState();
  }

  @override
  Widget build(BuildContext context) {
    const config = AppFlowyBoardConfig(
      groupBackgroundColor: Colors.white,
    );
    return AppFlowyBoard(
        controller: controller,
        cardBuilder: (context, group, groupItem) {
          return AppFlowyGroupCard(
            key: ValueKey(groupItem.id),
            child: _buildCard(groupItem),
          );
        },
        boardScrollController: boardController,
        footerBuilder: (context, columnData) {
          return AppFlowyGroupFooter(
            icon: const Icon(Icons.add, size: 20),
            title: const Text('New'),
            height: 50,
            margin: config.groupItemPadding,
            onAddButtonClick: () {
              boardController.scrollToBottom(columnData.id);
            },
          );
        },
        headerBuilder: (context, columnData) {
          return AppFlowyGroupHeader(
            icon: const Icon(Icons.lightbulb_circle),
            title: SizedBox(
              width: 150,
              child: TextField(
                controller: TextEditingController()
                  ..text = columnData.headerData.groupName,
                style: const TextStyle(
                    color: Colors.black,
                    fontFamily: "Ubuntu",
                    fontSize: 24,
                    fontWeight: FontWeight.bold),
                onSubmitted: (val) {
                  controller
                      .getGroupController(columnData.headerData.groupId)!
                      .updateGroupName(val);
                },
              ),
            ),
            addIcon: const Icon(Icons.add, size: 20),
            moreIcon: const Icon(Icons.more_horiz, size: 20),
            height: 50,
            margin: config.groupItemPadding,
          );
        },
        groupConstraints: const BoxConstraints.tightFor(width: 350),
        config: config);
  }

  Widget _buildCard(AppFlowyGroupItem item) {
    return Padding(
      padding: const EdgeInsets.all(8),
      child: BuildArtefactCard(item: item as BuildArtefactItem),
    );
  }
}
