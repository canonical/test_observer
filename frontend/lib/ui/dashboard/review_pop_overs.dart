import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:popover/popover.dart';
import 'package:yaru_widgets/yaru_widgets.dart';

import '../../models/artefact.dart';
import '../../models/artefact_build.dart';
import '../../models/test_execution.dart';
import '../../providers/artefact_builds.dart';
import '../spacing.dart';

class TestExecutionReviewButton extends StatelessWidget {
  const TestExecutionReviewButton({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(4),
      child: ElevatedButton(
        onPressed: () {
          showPopover(
            context: context,
            bodyBuilder: (context) => _TestExecutionPopOver(
              testExecution: testExecution,
            ),
            direction: PopoverDirection.bottom,
            width: 500,
            height: 300,
            arrowHeight: 15,
            arrowWidth: 30,
          );
        },
        child: const Text('Review'),
      ),
    );
  }
}

class _TestExecutionPopOver extends StatelessWidget {
  const _TestExecutionPopOver({required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          Text(
            'Select new review status',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text(
            'Insert review comments:',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const TextField(
            decoration: InputDecoration(
              border: OutlineInputBorder(),
              hintText: 'Insert review comments',
            ),
          ),
          const ElevatedButton(
            onPressed: null,
            child: Text('Submit Review'),
          ),
        ],
      ),
    );
  }
}

class ApproveArtefactButton extends ConsumerWidget {
  const ApproveArtefactButton({super.key, required this.artefact});

  final Artefact artefact;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactBuilds = ref.watch(artefactBuildsProvider(artefact.id));

    return artefactBuilds.when(
      data: (artefactBuilds) => Padding(
        padding: const EdgeInsets.all(4),
        child: ElevatedButton(
          onPressed: () {
            showPopover(
              context: context,
              bodyBuilder: (context) => _ArtefactReviewPopOver(
                artefact: artefact,
                artefactBuilds: artefactBuilds,
              ),
              direction: PopoverDirection.top,
              width: 350,
              height: 150,
              arrowHeight: 15,
              arrowWidth: 30,
            );
          },
          child: const Text('Approve Artefact'),
        ),
      ),
      loading: () => const Center(child: YaruCircularProgressIndicator()),
      error: (error, stackTrace) {
        return Center(child: Text('Error: $error'));
      },
    );
  }
}

class _ArtefactReviewPopOver extends StatelessWidget {
  const _ArtefactReviewPopOver({
    required this.artefact,
    required this.artefactBuilds,
  });
  final Artefact artefact;
  final List<ArtefactBuild> artefactBuilds;

  @override
  Widget build(BuildContext context) {
    if (artefactBuilds.any(
      (build) => build.testExecutions.any(
        (execution) =>
            execution.reviewStatus ==
                TestExecutionReviewStatus.markedAsFailed ||
            execution.reviewStatus == TestExecutionReviewStatus.undecided,
      ),
    )) {
      return _DisabledArtefactReviewPopOver();
    } else {
      return _EnabledArtefactReviewPopOver(artefactName: artefact.name);
    }
  }
}

class _EnabledArtefactReviewPopOver extends StatelessWidget {
  const _EnabledArtefactReviewPopOver({
    required this.artefactName,
  });
  final String artefactName;
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          RichText(
            textAlign: TextAlign.center,
            text: TextSpan(
              style: Theme.of(context).textTheme.titleMedium,
              children: [
                const TextSpan(
                  text: 'You are about to sign-off the ',
                ),
                TextSpan(
                  text: artefactName,
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
                const TextSpan(
                  text: ' artefact. Please confirm this action below.',
                ),
              ],
            ),
          ),
          const Padding(
            padding: EdgeInsets.all(Spacing.level4),
            child: ElevatedButton(
              onPressed: null,
              child: Text('Approve Artefact'),
            ),
          ),
        ],
      ),
    );
  }
}

class _DisabledArtefactReviewPopOver extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: ListView(
        padding: const EdgeInsets.all(8),
        children: [
          Text(
            'At least one Test Execution is marked as failed or undecided. Please approve all individual test executions before approving the whole artefact.',
            style: Theme.of(context).textTheme.titleMedium,
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}
