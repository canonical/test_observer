import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../providers/family_artefacts.dart';
import '../../routing.dart';
import '../dialog_header.dart';
import '../spacing.dart';
import 'artefact_page_body.dart';
import 'artefact_page_header.dart';
import 'artefact_page_side.dart';

class ArtefactPage extends ConsumerWidget {
  const ArtefactPage({super.key, required this.artefactId});

  final int artefactId;

  Column get _invalidArtefactErrorMessage {
    return const Column(
      children: [
        DialogHeader(),
        Expanded(
          child: Center(
            child: Text('Artefact not found. It may be that a'
                ' newer version has been released already'),
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final family = AppRoutes.familyFromUri(AppRoutes.uriFromContext(context));
    final artefacts = ref.watch(familyArtefactsProvider(family));
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: artefacts.when(
        data: (artefacts) {
          final artefact = artefacts[artefactId];
          if (artefact == null) return _invalidArtefactErrorMessage;
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
