// Copyright (C) 2023 Canonical Ltd.
//
// This file is part of Test Observer Frontend.
//
// Test Observer Frontend is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
//
// Test Observer Frontend is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';
import '../../models/artefact.dart';
import '../../providers/environments_issues.dart';
import '../../providers/filtered_artefact_environments.dart';
import '../../providers/tests_issues.dart';
import '../../routing.dart';
import '../non_blocking_provider_preloader.dart';
import '../spacing.dart';
import 'environment_expandable.dart';

class ArtefactPageBody extends ConsumerWidget {
  const ArtefactPageBody({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final pageUri = AppRoutes.uriFromContext(context);
    final environments = ref
        .watch(filteredArtefactEnvironmentsProvider(pageUri))
        .value
        ?.toList();

    if (environments == null) {
      return const Center(child: YaruCircularProgressIndicator());
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.baseline,
          textBaseline: TextBaseline.alphabetic,
          children: [
            Text(
              'Environments',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
          ],
        ),
        NonBlockingProviderPreloader(
          provider: environmentsIssuesProvider,
          child: NonBlockingProviderPreloader(
            provider: testsIssuesProvider,
            child: Expanded(
              child: ListView.builder(
                itemCount: environments.length,
                itemBuilder: (_, i) => Padding(
                  // Padding is to avoid scroll bar covering trailing buttons
                  padding: const EdgeInsets.only(right: Spacing.level3),
                  child: EnvironmentExpandable(
                    artefactEnvironment: environments[i],
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
