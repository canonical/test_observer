import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';
import 'package:yaru_widgets/yaru_widgets.dart';
import 'package:popover/popover.dart';

import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';

class TestExecutionReviewButton extends StatelessWidget {
  const TestExecutionReviewButton({
    super.key,
    required this.testExecution,
    required this.artefactId,
  });

  final TestExecution testExecution;
  final int artefactId;

  Text _getReviewDecisionText(BuildContext context) {
    final fontStyle = Theme.of(context).textTheme.labelMedium;
    if (testExecution.reviewDecision.isEmpty) {
      return Text(
        'Undecided',
        style: fontStyle?.apply(color: YaruColors.textGrey),
      );
    } else if (testExecution.reviewDecision
        .contains(TestExecutionReviewDecision.rejected)) {
      return Text(
        'Rejected',
        style: fontStyle?.apply(color: YaruColors.red),
      );
    } else {
      return Text(
        'Approved',
        style: fontStyle?.apply(color: YaruColors.light.success),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        showPopover(
          context: context,
          bodyBuilder: (context) => TestExecutionPopOver(
            testExecution: testExecution,
            artefactId: artefactId,
          ),
          direction: PopoverDirection.bottom,
          width: 500,
          height: 500,
          arrowHeight: 15,
          arrowWidth: 30,
        );
      },
      child: Chip(
        label: _getReviewDecisionText(context),
        shape: const StadiumBorder(),
      ),
    );
  }
}

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
  final reviewCommentController = TextEditingController();

  String reviewComment = '';
  List<TestExecutionReviewDecision> selectedDecision = [];
  Map<TestExecutionReviewDecision, bool> reviewDecisions = {};
  bool rejected = false;

  bool enableRejected = true;
  bool enableApproved = true;

  void updateCheckboxEnabledStatus() {
    enableApproved = enableRejected = true;
    for (final value in selectedDecision) {
      if (value == TestExecutionReviewDecision.rejected) {
        enableApproved = false;
      } else {
        enableRejected = false;
      }
    }
  }

  @override
  void initState() {
    super.initState();
    reviewComment = widget.testExecution.reviewComment;

    for (final value in TestExecutionReviewDecision.values) {
      reviewDecisions[value] =
          widget.testExecution.reviewDecision.contains(value);

      if (reviewDecisions[value] ?? false) {
        selectedDecision.add(value);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    updateCheckboxEnabledStatus();
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Text(
              'Select new review status:',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
          Column(
            children: TestExecutionReviewDecision.values
                .map(
                  (e) => YaruCheckboxListTile(
                    value: reviewDecisions[e],
                    onChanged: ((e == TestExecutionReviewDecision.rejected &&
                                (enableRejected)) ||
                            (e != TestExecutionReviewDecision.rejected &&
                                enableApproved))
                        ? (bool? value) {
                            setState(() {
                              reviewDecisions[e] = value!;

                              if (selectedDecision.contains(e)) {
                                selectedDecision.remove(e);
                              } else {
                                selectedDecision.add(e);
                              }
                            });

                            updateCheckboxEnabledStatus();
                          }
                        : null,
                    title: Text(e.name),
                  ),
                )
                .toList(),
          ),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Text(
              'Additional review comments:',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
          TextField(
            decoration: const InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Insert review comment',
            ),
            onChanged: (value) {
              setState(() {
                reviewComment = value;
              });
            },
          ),
          Padding(
            padding: const EdgeInsets.only(top: 8.0),
            child: ElevatedButton(
              onPressed: () => ref
                  .read(ArtefactBuildsProvider(widget.artefactId).notifier)
                  .changeReviewDecision(
                    widget.testExecution.id,
                    reviewComment,
                    selectedDecision,
                  ),
              child: const Text('Submit Review'),
            ),
          ),
        ],
      ),
    );
  }
}
