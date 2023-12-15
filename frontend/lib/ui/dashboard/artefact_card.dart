import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intersperse/intersperse.dart';

import '../../models/artefact.dart';
import '../spacing.dart';

class ArtefactCard extends ConsumerWidget {
  const ArtefactCard({Key? key, required this.artefact}) : super(key: key);

  final Artefact artefact;
  static const double width = 320;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
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
          height: 156,
          padding: const EdgeInsets.all(Spacing.level4),
          child: Column(
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
            ],
          ),
        ),
      ),
    );
  }
}
