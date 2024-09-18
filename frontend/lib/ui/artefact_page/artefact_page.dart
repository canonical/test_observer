import 'package:flutter/material.dart';

import '../../providers/artefact.dart';
import '../blocking_provider_preloader.dart';
import '../spacing.dart';
import 'artefact_page_body.dart';
import 'artefact_page_header.dart';
import 'artefact_page_side.dart';

class ArtefactPage extends StatelessWidget {
  const ArtefactPage({super.key, required this.artefactId});

  final int artefactId;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(
        left: Spacing.pageHorizontalPadding,
        right: Spacing.pageHorizontalPadding,
        top: Spacing.level5,
      ),
      child: BlockingProviderPreloader(
        provider: artefactProvider(artefactId),
        builder: (_, artefact) => Column(
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
        ),
      ),
    );
  }
}
