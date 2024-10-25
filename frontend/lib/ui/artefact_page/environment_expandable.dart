import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';

import '../../models/artefact_environment.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'environment_issues/environment_issues_expandable.dart';
import 'environment_review_button.dart';
import 'test_execution_expandable/test_execution_expandable.dart';

class EnvironmentExpandable extends StatelessWidget {
  const EnvironmentExpandable({super.key, required this.artefactEnvironment});

  final ArtefactEnvironment artefactEnvironment;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      title: _EnvironmentExpandableTitle(
        artefactEnvironment: artefactEnvironment,
      ),
      children: [
        EnvironmentIssuesExpandable(
          environment: artefactEnvironment.environment,
        ),
        ...artefactEnvironment.runsDescending.mapIndexed(
          (i, te) => TestExecutionExpandable(
            initiallyExpanded: i == 0,
            testExecution: te,
            runNumber: artefactEnvironment.runsDescending.length - i,
          ),
        ),
      ],
    );
  }
}

class _EnvironmentExpandableTitle extends StatelessWidget {
  const _EnvironmentExpandableTitle({required this.artefactEnvironment});

  final ArtefactEnvironment artefactEnvironment;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(
          artefactEnvironment.architecture,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const SizedBox(width: Spacing.level4),
        Text(
          artefactEnvironment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        EnvironmentReviewButton(environmentReview: artefactEnvironment.review),
      ],
    );
  }
}
