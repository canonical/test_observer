import 'package:flutter/material.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_builds.dart';
import '../blocking_provider_preloader.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'artefact_page_info_section.dart';

class ArtefactPageSide extends StatelessWidget {
  const ArtefactPageSide({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 300.0,
      child: Column(
        children: [
          ArtefactPageInfoSection(artefact: artefact),
          const SizedBox(height: Spacing.level4),
          Expanded(
            child: _ArtefactPageSideFilters(artefact: artefact),
          ),
        ],
      ),
    );
  }
}

class _ArtefactPageSideFilters extends StatelessWidget {
  const _ArtefactPageSideFilters({required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context) {
    return BlockingProviderPreloader(
      provider: artefactBuildsProvider(artefact.id),
      builder: (_, artefactBuilds) => const PageFiltersView(
        searchHint: 'Search by environment name',
        width: double.infinity,
      ),
    );
  }
}
