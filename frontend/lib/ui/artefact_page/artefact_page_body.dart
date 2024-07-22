import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../page_filters/page_filters.dart';
import '../spacing.dart';
import 'artefact_build_expandable.dart';
import 'rerun_filtered_environments_button.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody(
      {super.key, required this.artefact, required this.artefactBuilds});

  final Artefact artefact;
  final List<ArtefactBuild> artefactBuilds;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const PageFiltersView(searchHint: 'Search by environment name'),
        const SizedBox(width: Spacing.level5),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: Spacing.level3),
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                textBaseline: TextBaseline.alphabetic,
                children: [
                  Text(
                    'Environments (${artefact.completedTestExecutionsCount}/${artefact.allTestExecutionsCount})',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const Spacer(),
                  const RerunFilteredEnvironmentsButton(),
                ],
              ),
              Expanded(
                child: ListView.builder(
                  itemCount: artefactBuilds.length,
                  itemBuilder: (_, i) => Padding(
                    // Padding is to avoid scroll bar covering trailing buttons
                    padding: const EdgeInsets.only(right: Spacing.level3),
                    child: ArtefactBuildExpandable(
                      artefactBuild: artefactBuilds[i],
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
