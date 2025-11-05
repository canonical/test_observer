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

import '../../models/artefact.dart';
import '../../providers/artefact_builds.dart';
import '../../providers/artefact_environment_reviews.dart';
import '../blocking_provider_preloader.dart';
import '../page_filters/artefact_filters_view.dart';
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
        crossAxisAlignment: CrossAxisAlignment.start,
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
      builder: (_, artefactBuilds) => BlockingProviderPreloader(
        provider: artefactEnvironmentReviewsProvider(artefact.id),
        builder: (_, environmentReviews) => const ArtefactFiltersView(
          width: double.infinity,
        ),
      ),
    );
  }
}
