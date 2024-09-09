import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../providers/artefact.dart';
import '../spacing.dart';
import 'artefact_page_body.dart';
import 'artefact_page_header.dart';
import 'artefact_page_side.dart';

class ArtefactPage extends ConsumerWidget {
  const ArtefactPage({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefact = ref.watch(artefactProvider(artefactId));
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: artefact.when(
        data: (artefact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              ArtefactPageHeader(artefact: artefact),
              const SizedBox(height: Spacing.level4),
              Expanded(
                child: Row(
                  children: [
                    ArtefactPageSide(artefact: artefact),
                    Expanded(child: ArtefactPageBody(artefact: artefact)),
                  ],
                ),
              ),
            ],
          );
        },
        error: (e, stack) =>
            Center(child: Text('Error:\n$e\nStackTrace:\n$stack')),
        loading: () => const Center(child: YaruCircularProgressIndicator()),
      ),
    );
  }
}
