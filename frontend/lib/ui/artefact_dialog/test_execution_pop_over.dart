import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../spacing.dart';

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
                (e) => YaruCheckboxListTile(
                  value: reviewDecisions.contains(e),
                  onChanged: ((e == TestExecutionReviewDecision.rejected &&
                              (_canReject)) ||
                          (e != TestExecutionReviewDecision.rejected &&
                              _canApprove))
                      ? (bool? value) {
                          setState(() {
                            if (reviewDecisions.contains(e)) {
                              reviewDecisions.remove(e);
                            } else {
                              reviewDecisions.add(e);
                            }
                          });
                        }
                      : null,
                  title: Text(e.name),
                ),
              )
              .toList(),
        ),
        const SizedBox(height: Spacing.level4),
        Text(
          'Additional review comments:',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(height: Spacing.level3),
        TextField(
          decoration: const InputDecoration(
            border: OutlineInputBorder(),
            hintText: 'Insert review comment',
          ),
          controller: reviewCommentController,
          keyboardType: TextInputType.multiline,
          maxLines: null,
        ),
        const SizedBox(height: Spacing.level3),
        ElevatedButton(
          onPressed: () => ref
              .read(ArtefactBuildsProvider(widget.artefactId).notifier)
              .changeReviewDecision(
                widget.testExecution.id,
                reviewCommentController.text,
                reviewDecisions,
              ),
          child: const Text('Submit Review'),
        ),
      ],
    );
  }
}
