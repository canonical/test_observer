import 'package:appflowy_board/appflowy_board.dart';
import 'package:flutter/material.dart';

import 'build_status.dart';

class BuildArtefactItem extends AppFlowyGroupItem {
  String package;
  String version;
  String revision;
  String channel;
  int observedCount = 30;
  int expectedCount = 30;

  BuildArtefactItem({
    this.package = "core20",
    this.version = "20221216",
    this.revision = "1762",
    this.channel = "latest",
    this.observedCount = 30,
    this.expectedCount = 30,
  });

  @override
  String get id => "$package - $version - ($revision) - [$channel]";

  BuildStatus getStatus() {
    if (observedCount / expectedCount < 0.2) {
      return BuildStatus.failed;
    }

    if (observedCount / expectedCount > 0.8) {
      return BuildStatus.success;
    }

    return BuildStatus.inProgress;
  }
}

class BuildArtefactCard extends StatelessWidget {
  final BuildArtefactItem item;
  const BuildArtefactCard({
    required this.item,
    Key? key,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
        height: 117,
        width: 307,
        decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(width: 1, color: const Color(0xffF6F6F5)),
            boxShadow: [
              BoxShadow(
                  blurRadius: 10,
                  color: Colors.grey.withOpacity(0.2),
                  offset: const Offset(4, 4))
            ]),
        child: Row(children: [
          BuildArtefactStatus(item: item),
          BuildInformation(item: item),
          const SizedBox(width: 120),
          Padding(
            padding: const EdgeInsets.only(bottom: 67),
            child: ExecutionCounts(item: item),
          ),
        ]));
  }
}

class BuildInformation extends StatelessWidget {
  final BuildArtefactItem item;

  const BuildInformation({required this.item, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        left: 20,
        top: 15,
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Text(
            item.package,
            style: const TextStyle(
              color: Colors.black,
              fontFamily: "Ubuntu",
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          )
        ]),
        Row(children: [
          Text(
            item.version,
            style: const TextStyle(
              color: Colors.black,
              fontFamily: "Ubuntu",
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          )
        ]),
        Row(children: [
          Text(
            "(${item.revision})",
            style: const TextStyle(
              color: Colors.black,
              fontFamily: "Ubuntu",
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          )
        ]),
        Row(children: [
          Text(
            "[${item.channel}]",
            style: const TextStyle(
              color: Colors.black,
              fontFamily: "Ubuntu",
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          )
        ])
      ]),
    );
  }
}

class ExecutionCounts extends StatelessWidget {
  final BuildArtefactItem item;

  const ExecutionCounts({required this.item, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Text("${item.observedCount.toString()}/${item.expectedCount.toString()}",
          style: const TextStyle(
            color: Colors.black,
            fontFamily: "Ubuntu",
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ))
    ]);
  }
}

class BuildArtefactStatus extends StatelessWidget {
  final BuildArtefactItem item;

  const BuildArtefactStatus({required this.item, Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 117,
      width: 7,
      decoration: BoxDecoration(
        color: item.getStatus().color,
      ),
    );
  }
}
