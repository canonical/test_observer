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

import '../../models/artefact_environment.dart';
import '../../providers/selected_environments.dart';
import '../spacing.dart';
import 'bulk_environment_review_dialog.dart';

class BulkEnvironmentSelectionControls extends ConsumerWidget {
  const BulkEnvironmentSelectionControls({
    super.key,
    required this.environments,
    required this.artefactId,
  });

  final List<ArtefactEnvironment> environments;
  final int artefactId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selectedCount = ref.watch(selectedEnvironmentsProvider).length;
    final totalCount = environments.length;

    // Get the selected environments and their reviews
    final selectedEnvironmentIds = ref.watch(selectedEnvironmentsProvider);
    final selectedEnvironments = environments
        .where((env) => selectedEnvironmentIds.contains(env.environment.id))
        .toList();
    final selectedReviews =
        selectedEnvironments.map((env) => env.review).toList();

    return Row(
      children: [
        Text(
          '$selectedCount of $totalCount selected',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(width: Spacing.level4),
        TextButton.icon(
          onPressed: () {
            ref.read(selectedEnvironmentsProvider.notifier).selectAll(
                  environments.map((e) => e.environment.id).toList(),
                );
          },
          label: const Text('Select All'),
        ),
        const SizedBox(width: Spacing.level2),
        TextButton.icon(
          onPressed: () {
            ref.read(selectedEnvironmentsProvider.notifier).deselectAll();
          },
          label: const Text('Deselect All'),
        ),
        const SizedBox(width: Spacing.level4),
        FilledButton.icon(
          onPressed: selectedCount == 0
              ? null
              : () {
                  showBulkEnvironmentReviewDialog(
                    context: context,
                    artefactId: artefactId,
                    environments: selectedEnvironments,
                    environmentReviews: selectedReviews,
                  );
                },
          icon: const Icon(Icons.rate_review, size: 18),
          label: Text(
            'Review $selectedCount environment${selectedCount != 1 ? 's' : ''}',
          ),
        ),
      ],
    );
  }
}
