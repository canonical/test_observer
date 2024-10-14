import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../models/environment_review.dart';
import '../../providers/artefact_environment_reviews.dart';
import '../spacing.dart';
import '../vanilla/vanilla_text_input.dart';

class EnvironmentReviewPopOver extends ConsumerStatefulWidget {
  const EnvironmentReviewPopOver({
    super.key,
    required this.environmentReview,
    required this.artefactId,
  });

  final EnvironmentReview environmentReview;
  final int artefactId;

  @override
  EnvironmentReviewPopOverState createState() =>
      EnvironmentReviewPopOverState();
}

class EnvironmentReviewPopOverState
    extends ConsumerState<EnvironmentReviewPopOver> {
  TextEditingController reviewCommentController = TextEditingController();
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
    reviewCommentController.text = widget.environmentReview.reviewComment;
    reviewDecisions = List.from(widget.environmentReview.reviewDecision);
  }

  @override
  void dispose() {
    reviewCommentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(12),
      children: [
        Text(
          'Select new review status:',
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
          label: 'Additional review comments:',
          labelStyle: Theme.of(context).textTheme.titleLarge,
          controller: reviewCommentController,
          multiline: true,
          hintText: 'Insert review comment',
        ),
        const SizedBox(height: Spacing.level3),
        ElevatedButton(
          onPressed: () {
            ref
                .read(
                  artefactEnvironmentReviewsProvider(widget.artefactId)
                      .notifier,
                )
                .updateReview(
                  widget.environmentReview.copyWith(
                    reviewDecision: reviewDecisions,
                    reviewComment: reviewCommentController.text,
                  ),
                );
            Navigator.pop(context);
          },
          child: const Text('Submit Review'),
        ),
      ],
    );
  }
}
