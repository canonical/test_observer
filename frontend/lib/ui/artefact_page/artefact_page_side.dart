import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_builds.dart';
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
            child: Consumer(
              builder: (context, ref, child) {
                final artefactBuilds =
                    ref.watch(artefactBuildsProvider(artefact.id));

                return artefactBuilds.when(
                  loading: () => const YaruCircularProgressIndicator(),
                  error: (e, stack) =>
                      Center(child: Text('Error:\n$e\nStackTrace:\n$stack')),
                  data: (artefactBuilds) => const PageFiltersView(
                    searchHint: 'Search by environment name',
                    width: double.infinity,
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
