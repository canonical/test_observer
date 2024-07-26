import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../spacing.dart';
import '../user_avatar.dart';
import '../vanilla/vanilla_chip.dart';

class ArtefactCard extends ConsumerWidget {
  const ArtefactCard({Key? key, required this.artefact}) : super(key: key);

  final Artefact artefact;
  static const double width = 320;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final assignee = artefact.assignee;
    final dueDate = artefact.dueDateString;

    return GestureDetector(
      onTap: () {
        final currentRoute = GoRouterState.of(context).fullPath;
        context.go('$currentRoute/${artefact.id}');
      },
      child: Card(
        margin: const EdgeInsets.all(0),
        elevation: 0,
        shape: RoundedRectangleBorder(
          side: BorderSide(color: Theme.of(context).colorScheme.outline),
          borderRadius: BorderRadius.circular(2.25),
        ),
        child: Container(
          width: width,
          height: 182,
          padding: const EdgeInsets.all(Spacing.level4),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                artefact.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: Spacing.level2),
              ...artefact.details.entries
                  .map<Widget>(
                    (detail) => Text('${detail.key}: ${detail.value}'),
                  )
                  .intersperse(const SizedBox(height: Spacing.level2)),
              const SizedBox(height: Spacing.level2),
              Row(
                children: [
                  VanillaChip(
                    text: artefact.status.name,
                    fontColor: artefact.status.color,
                  ),
                  const Spacer(),
                  if (dueDate != null)
                    VanillaChip(
                      text: 'Due $dueDate',
                      fontColor: YaruColors.red,
                    ),
                  const Spacer(),
                  if (assignee != null)
                    UserAvatar(
                      user: assignee,
                      allTestExecutionsCount: artefact.allTestExecutionsCount,
                      completedTestExecutionsCount:
                          artefact.completedTestExecutionsCount,
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
