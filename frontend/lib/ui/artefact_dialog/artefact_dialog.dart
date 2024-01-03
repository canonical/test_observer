import 'dart:math';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/widgets.dart';

import '../../providers/artefacts.dart';
import '../dialog_header.dart';
import '../spacing.dart';
import 'artefact_dialog_body.dart';
import 'artefact_dialog_header.dart';
import 'artefact_dialog_info_section.dart';

class ArtefactDialog extends ConsumerWidget {
  const ArtefactDialog({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefacts = ref.watch(artefactsProvider);

    return SelectionArea(
      child: Dialog(
        child: SizedBox(
          height: min(800, MediaQuery.of(context).size.height * 0.8),
          width: min(1200, MediaQuery.of(context).size.width * 0.8),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: Spacing.level5,
              vertical: Spacing.level3,
            ),
            child: artefacts.when(
              data: (artefacts) {
                final artefact = artefacts[artefactId];

                if (artefact == null) {
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

                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ArtefactDialogHeader(artefact: artefact),
                    const SizedBox(height: Spacing.level4),
                    ArtefactDialogInfoSection(artefact: artefact),
                    const SizedBox(height: Spacing.level4),
                    Expanded(child: ArtefactDialogBody(artefact: artefact)),
                  ],
                );
              },
              loading: () =>
                  const Center(child: YaruCircularProgressIndicator()),
              error: (error, stackTrace) =>
                  Text('Failed to fetch artefact $artefactId $error'),
            ),
          ),
        ),
      ),
    );
  }
}
