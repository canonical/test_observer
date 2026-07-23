// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../models/artefact.dart';
import '../../providers/artefact_environment_reviews.dart';
import '../spacing.dart';
import '../reviewers_avatars.dart';
import 'artefact_signoff_button.dart';

class ArtefactPageHeader extends ConsumerWidget {
  const ArtefactPageHeader({super.key, required this.artefact});

  final Artefact artefact;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dueDate = artefact.dueDateString;
    final environmentReviewsAsync =
        ref.watch(artefactEnvironmentReviewsProvider(artefact.id));
    final environmentReviews = environmentReviewsAsync.valueOrNull ?? const [];

    return Row(
      children: [
        Text(artefact.name, style: Theme.of(context).textTheme.headlineLarge),
        const SizedBox(width: Spacing.level4),
        ArtefactSignoffButton(artefact: artefact),
        const SizedBox(width: Spacing.level4),
        ReviewersAvatars(
          reviewers: artefact.reviewers,
          allEnvironmentReviewsCount: artefact.allEnvironmentReviewsCount,
          completedEnvironmentReviewsCount:
              artefact.completedEnvironmentReviewsCount,
          environmentReviews: environmentReviews,
        ),
        const SizedBox(width: Spacing.level4),
        if (dueDate != null)
          Text(
            'Due $dueDate',
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.apply(color: YaruColors.red),
          ),
      ],
    );
  }
}
