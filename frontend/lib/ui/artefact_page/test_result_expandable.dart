import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intersperse/intersperse.dart';
import 'package:yaru/widgets.dart';

import '../../models/test_result.dart';
import '../../providers/artefact.dart';
import '../../providers/test_result_issues.dart';
import '../../routing.dart';
import '../expandable.dart';
import '../spacing.dart';
import 'test_issues/test_issues_expandable.dart';

class TestResultExpandable extends ConsumerWidget {
  const TestResultExpandable({super.key, required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final issues = ref.watch(testResultIssuesProvider(testResult)).value ?? [];

    String title = testResult.name;
    if (issues.length == 1) {
      title += ' (${issues.length} reported issue)';
    } else if (issues.length > 1) {
      title += ' (${issues.length} reported issues)';
    }

    return Expandable(
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          _PreviousTestResultsWidget(
            currentResult: testResult,
            previousResults: testResult.previousResults,
          ),
        ],
      ),
      children: [
        TestIssuesExpandable(testResult: testResult),
        _TestResultOutputExpandable(testResult: testResult),
      ],
    );
  }
}

class _TestResultOutputExpandable extends StatelessWidget {
  const _TestResultOutputExpandable({required this.testResult});

  final TestResult testResult;

  @override
  Widget build(BuildContext context) {
    return Expandable(
      title: const Text('Details'),
      initiallyExpanded: true,
      children: [
        if (testResult.category != '')
          YaruTile(
            title: const Text('Category'),
            subtitle: Text(testResult.category),
          ),
        if (testResult.comment != '')
          YaruTile(
            title: const Text('Comment'),
            subtitle: Text(testResult.comment),
          ),
        if (testResult.ioLog != '')
          YaruTile(
            title: const Text('IO Log'),
            subtitle: Text(testResult.ioLog),
          ),
      ],
    );
  }
}

class _PreviousTestResultsWidget extends ConsumerWidget {
  const _PreviousTestResultsWidget({
    required this.currentResult,
    required this.previousResults,
  });

  final TestResult currentResult;
  final List<PreviousTestResult> previousResults;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefactId =
        AppRoutes.artefactIdFromUri(AppRoutes.uriFromContext(context));
    final currentVersion = ref
            .watch(
              artefactProvider(artefactId)
                  .select((data) => data.whenData((a) => a.version)),
            )
            .value ??
        '';

    final statusGroups = {
      currentVersion: [
        PreviousTestResult(
          artefactId: artefactId,
          status: currentResult.status,
          version: currentVersion,
        ),
      ],
    };
    for (final result in previousResults) {
      final statuses = statusGroups[result.version];
      if (statuses != null) {
        statuses.add(result);
      } else {
        statusGroups[result.version] = [result];
      }
    }

    return Row(
      children: statusGroups.entries
          .mapIndexed<Widget>(
            (groupIndex, entry) => InkWell(
              onTap: (groupIndex > 0)
                  ? () => navigateToArtefactPage(
                        context,
                        entry.value.first.artefactId,
                      )
                  : null,
              child: Tooltip(
                message: 'Version: ${entry.key}',
                child: Wrap(
                  crossAxisAlignment: WrapCrossAlignment.center,
                  spacing: -5,
                  children: entry.value
                      .mapIndexed(
                        (index, result) => Container(
                          decoration: const BoxDecoration(
                            color: Colors.white,
                            shape: BoxShape.circle,
                          ),
                          child: result.status.getIcon(
                            scale:
                                (groupIndex == index && index == 0) ? 1.5 : 1,
                          ),
                        ),
                      )
                      .reversed
                      .toList(),
                ),
              ),
            ),
          )
          .reversed
          .intersperse(const SizedBox(width: Spacing.level2))
          .toList(),
    );
  }
}
