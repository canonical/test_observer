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

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

import '../../models/test_result.dart';
import '../../providers/test_results.dart';
import '../blocking_provider_preloader.dart';
import '../expandable.dart';
import 'test_result_expandable.dart';

class TestResultsFilterExpandable extends StatelessWidget {
  const TestResultsFilterExpandable({
    super.key,
    required this.statusToFilterBy,
    required this.testExecutionId,
    required this.artefactId,
  });

  final TestResultStatus statusToFilterBy;
  final int testExecutionId;
  final int artefactId;

  @override
  Widget build(BuildContext context) {
    Color? fontColor;
    if (statusToFilterBy == TestResultStatus.failed) {
      fontColor = YaruColors.red;
    } else if (statusToFilterBy == TestResultStatus.passed) {
      fontColor = YaruColors.light.success;
    }

    final headerStyle =
        Theme.of(context).textTheme.titleMedium?.apply(color: fontColor);

    return BlockingProviderPreloader(
      provider: testResultsProvider(testExecutionId),
      builder: (_, testResults) {
        final filteredTestResults = testResults
            .filter((testResult) => testResult.status == statusToFilterBy)
            .toList();

        return Expandable(
          initiallyExpanded: statusToFilterBy == TestResultStatus.failed &&
              filteredTestResults.isNotEmpty,
          title: Text(
            '${statusToFilterBy.name} ${filteredTestResults.length}',
            style: headerStyle,
          ),
          children: filteredTestResults
              .map(
                (testResult) => TestResultExpandable(
                  testExecutionId: testExecutionId,
                  testResult: testResult,
                  artefactId: artefactId,
                ),
              )
              .toList(),
        );
      },
    );
  }
}
