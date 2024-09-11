import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/widgets.dart';

import '../../models/test_execution.dart';
import '../../providers/review_test_execution.dart';
import '../spacing.dart';
import '../vanilla/vanilla_text_input.dart';

class TestExecutionPopOver extends ConsumerStatefulWidget {
  const TestExecutionPopOver({
    super.key,
    required this.testExecution,
    required this.artefactId,
  });

  final TestExecution testExecution;
  final int artefactId;

  @override
  TestExecutionPopOverState createState() => TestExecutionPopOverState();
}

class TestExecutionPopOverState extends ConsumerState<TestExecutionPopOver> {
  TextEditingController reviewCommentController = TextEditingController();
  List<TestExecutionReviewDecision> reviewDecisions = [];

  bool get _canApprove {
    return !reviewDecisions.contains(TestExecutionReviewDecision.rejected);
  }

  bool get _canReject {
    return reviewDecisions.isEmpty ||
        reviewDecisions.contains(TestExecutionReviewDecision.rejected);
  }

  Function(bool?)? getOnChangedCheckboxListTileFunction(
    TestExecutionReviewDecision testExecutionReviewDecision,
  ) {
    // Ensure the test execution cannot be rejected and approved in the same time
    final bool enableCheckboxConsistencyCheck = (testExecutionReviewDecision ==
                TestExecutionReviewDecision.rejected &&
            _canReject) ||
        (testExecutionReviewDecision != TestExecutionReviewDecision.rejected &&
            _canApprove);
    if (!testExecutionReviewDecision.isDeprecated &&
        enableCheckboxConsistencyCheck) {
      return (bool? value) {
        setState(() {
          if (reviewDecisions.contains(testExecutionReviewDecision)) {
            reviewDecisions.remove(testExecutionReviewDecision);
          } else {
            reviewDecisions.add(testExecutionReviewDecision);
          }
        });
      };
    }
    return null;
  }

  bool shouldDisplayDecision(TestExecutionReviewDecision decision) {
    return !decision.isDeprecated || reviewDecisions.contains(decision);
  }

  @override
  void initState() {
    super.initState();
    reviewCommentController.text = widget.testExecution.reviewComment;
    reviewDecisions = List.from(widget.testExecution.reviewDecision);
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
          children: TestExecutionReviewDecision.values
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
            ref.read(reviewTestExecutionProvider.notifier).reviewTestExecution(
                  widget.testExecution.id,
                  reviewCommentController.text,
                  reviewDecisions,
                  widget.artefactId,
                );
            Navigator.pop(context);
          },
          child: const Text('Submit Review'),
        ),
      ],
    );
  }
}
