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
import 'package:yaru/widgets.dart';

import '../../models/artefact_environment.dart';
import '../../models/environment_review.dart';
import '../../providers/review_environment.dart';
import '../spacing.dart';
import '../vanilla/vanilla_text_input.dart';

class BulkEnvironmentReviewDialog extends ConsumerStatefulWidget {
  const BulkEnvironmentReviewDialog({
    super.key,
    required this.artefactId,
    required this.environments,
    required this.environmentReviews,
  });

  final int artefactId;
  final List<ArtefactEnvironment> environments;
  final List<EnvironmentReview> environmentReviews;

  @override
  ConsumerState<BulkEnvironmentReviewDialog> createState() =>
      _BulkEnvironmentReviewDialogState();
}

class _BulkEnvironmentReviewDialogState
    extends ConsumerState<BulkEnvironmentReviewDialog> {
  late TextEditingController reviewCommentController;
  List<EnvironmentReviewDecision> reviewDecisions = [];

  bool get _canApprove {
    return !reviewDecisions.contains(EnvironmentReviewDecision.rejected);
  }

  bool get _canReject {
    return reviewDecisions.isEmpty ||
        reviewDecisions.contains(EnvironmentReviewDecision.rejected);
  }

  Function(bool?)? getOnChangedCheckboxListTileFunction(
    EnvironmentReviewDecision reviewDecision,
  ) {
    // Ensure the environment cannot be rejected and approved in the same time
    final bool enableCheckboxConsistencyCheck =
        (reviewDecision == EnvironmentReviewDecision.rejected && _canReject) ||
            (reviewDecision != EnvironmentReviewDecision.rejected &&
                _canApprove);
    if (!reviewDecision.isDeprecated && enableCheckboxConsistencyCheck) {
      return (bool? value) {
        setState(() {
          if (reviewDecisions.contains(reviewDecision)) {
            reviewDecisions.remove(reviewDecision);
          } else {
            reviewDecisions.add(reviewDecision);
          }
        });
      };
    }
    return null;
  }

  bool shouldDisplayDecision(EnvironmentReviewDecision decision) {
    return !decision.isDeprecated || reviewDecisions.contains(decision);
  }

  @override
  void initState() {
    super.initState();
    reviewCommentController = TextEditingController();
  }

  @override
  void dispose() {
    reviewCommentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Bulk Environment Review'),
      content: SizedBox(
        width: 500,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Applying review to ${widget.environments.length} environment${widget.environments.length != 1 ? 's' : ''}:',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: Spacing.level2),
            Container(
              decoration: BoxDecoration(
                border: Border.all(color: Colors.grey[300]!),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  for (var i = 0; i < widget.environments.length; i++) ...[
                    Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: Spacing.level2,
                        vertical: Spacing.level1,
                      ),
                      child: Align(
                        alignment: Alignment.centerLeft,
                        child: Text(
                          '${widget.environments[i].environment.name} '
                          '(${widget.environments[i].environment.architecture})',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ),
                    if (i != widget.environments.length - 1)
                      Divider(height: 1, color: Colors.grey[300]),
                  ],
                ],
              ),
            ),
            const SizedBox(height: Spacing.level4),
            Text(
              'Select review status:',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: Spacing.level3),
            Column(
              children: EnvironmentReviewDecision.values
                  .map(
                    (e) => shouldDisplayDecision(e)
                        ? YaruCheckboxListTile(
                            value: reviewDecisions.contains(e),
                            onChanged: getOnChangedCheckboxListTileFunction(e),
                            title: Text(e.name),
                          )
                        : null,
                  )
                  .whereType<YaruCheckboxListTile>()
                  .toList(),
            ),
            const SizedBox(height: Spacing.level4),
            VanillaTextInput(
              label: 'Additional review comment:',
              labelStyle: Theme.of(context).textTheme.titleLarge,
              controller: reviewCommentController,
              multiline: true,
              hintText: 'Insert review comment',
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: () {
            // Apply the same review comment and decisions to all selected environments
            final updatedReviews = widget.environmentReviews
                .map(
                  (review) => review.copyWith(
                    reviewDecision: reviewDecisions,
                    reviewComment: reviewCommentController.text,
                  ),
                )
                .toList();

            ref.read(reviewEnvironmentProvider.notifier).bulkReview(
                  updatedReviews,
                  widget.artefactId,
                );
            Navigator.pop(context);
          },
          child: const Text('Submit Reviews'),
        ),
      ],
    );
  }
}

void showBulkEnvironmentReviewDialog({
  required BuildContext context,
  required int artefactId,
  required List<ArtefactEnvironment> environments,
  required List<EnvironmentReview> environmentReviews,
}) =>
    showDialog(
      context: context,
      builder: (_) => BulkEnvironmentReviewDialog(
        artefactId: artefactId,
        environments: environments,
        environmentReviews: environmentReviews,
      ),
    );
