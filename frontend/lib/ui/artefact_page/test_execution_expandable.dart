import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../models/test_execution.dart';
import '../../models/test_result.dart';
import '../../providers/artefact_builds.dart';
import '../../routing.dart';
import '../inline_url_text.dart';
import '../spacing.dart';
import 'test_execution_review.dart';
import 'test_result_filter_expandable.dart';
import 'test_event_log_expandable.dart';

class TestExecutionExpandable extends ConsumerWidget {
  const TestExecutionExpandable({super.key, required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (!testExecution.status.isCompleted) {
      return ExpansionTile(
        controlAffinity: ListTileControlAffinity.leading,
        childrenPadding: const EdgeInsets.only(left: Spacing.level4),
        shape: const Border(),
        title: _TestExecutionTileTitle(testExecution: testExecution),
        children: <Widget>[
          TestEventLogExpandable(testExecutionId: testExecution.id, initiallyExpanded: true),          
        ],
      );
    }

    return ExpansionTile(
      controlAffinity: ListTileControlAffinity.leading,
      childrenPadding: const EdgeInsets.only(left: Spacing.level4),
      shape: const Border(),
      title: _TestExecutionTileTitle(testExecution: testExecution),
      children: <Widget>[
        TestEventLogExpandable(testExecutionId: testExecution.id, initiallyExpanded: false),
        ExpansionTile(
          controlAffinity: ListTileControlAffinity.leading,
          childrenPadding: const EdgeInsets.only(left: Spacing.level4),
          shape: const Border(),
          title: const Text('Test Results'),
          initiallyExpanded: true,
          children: TestResultStatus.values
          .map(
            (status) => TestResultsFilterExpandable(
              statusToFilterBy: status,
              testExecutionId: testExecution.id,
            ),
          )
          .toList(),
        ),
      ],
    );
  }
}

class _TestExecutionTileTitle extends StatelessWidget {
  const _TestExecutionTileTitle({required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context) {
    final ciLink = testExecution.ciLink;
    final c3Link = testExecution.c3Link;

    return Row(
      children: [
        if (!testExecution.status.isCompleted) const SizedBox(width: 36.0),
        testExecution.status.icon,
        const SizedBox(width: Spacing.level4),
        Text(
          testExecution.environment.name,
          style: Theme.of(context).textTheme.titleLarge,
        ),
        const Spacer(),
        _RerunButton(testExecution: testExecution),
        const SizedBox(width: Spacing.level3),
        TestExecutionReviewButton(testExecution: testExecution),
        const SizedBox(width: Spacing.level4),
        if (ciLink != null)
          InlineUrlText(
            url: ciLink,
            urlText: 'CI',
          ),
        const SizedBox(width: Spacing.level3),
        if (c3Link != null)
          InlineUrlText(
            url: c3Link,
            urlText: 'C3',
          ),
      ],
    );
  }
}

class _RerunButton extends ConsumerWidget {
  const _RerunButton({required this.testExecution});

  final TestExecution testExecution;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));

    final handlePress = testExecution.isRerunRequested
        ? null
        : () => showDialog(
              context: context,
              builder: (_) => _RerunConfirmationDialog(
                artefactId: artefactId,
                testExecutionId: testExecution.id,
              ),
            );

    return Tooltip(
      message: testExecution.isRerunRequested ? 'Already requested' : '',
      child: TextButton(
        onPressed: handlePress,
        child: const Text('rerun'),
      ),
    );
  }
}

class _RerunConfirmationDialog extends ConsumerWidget {
  const _RerunConfirmationDialog({
    required this.artefactId,
    required this.testExecutionId,
  });

  final int artefactId;
  final int testExecutionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return AlertDialog(
      title: const Text(
        'Are you sure you want to rerun this environment?',
      ),
      actions: [
        TextButton(
          autofocus: true,
          onPressed: () {
            ref
                .read(artefactBuildsProvider(artefactId).notifier)
                .rerunTestExecutions({testExecutionId});
            context.pop();
          },
          child: const Text('yes'),
        ),
        TextButton(
          onPressed: () => context.pop(),
          child: const Text('no'),
        ),
      ],
    );
  }
}
