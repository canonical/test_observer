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

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/material.dart';

import '../../../../models/attachment_rule_filters.dart';
import '../../../../models/execution_metadata.dart';
import '../../../../models/test_result.dart';
import '../../../../providers/artefact_builds.dart';
import '../../../../providers/artefact.dart';
import '../../../attachment_rule.dart';

class AttachmentRuleSection extends ConsumerWidget {
  const AttachmentRuleSection({
    super.key,
    required this.artefactId,
    required this.testResult,
    required this.testExecutionId,
    required this.selectedFilters,
    required this.onChanged,
  });

  final int artefactId;
  final TestResult? testResult;
  final int testExecutionId;
  final AttachmentRuleFilters selectedFilters;
  final ValueChanged<AttachmentRuleFilters> onChanged;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final artefact = ref.read(artefactProvider(artefactId)).value;
    final familyName = artefact?.family ?? '';
    final templateId = testResult?.templateId ?? '';
    final testCaseName = testResult?.name ?? '';
    final testExecution = ref
        .read(
          artefactBuildsProvider(artefactId).select(
            (value) => value.whenData(
              (builds) =>
                  builds.expand((build) => build.testExecutions).firstWhere(
                        (te) => te.id == testExecutionId,
                      ),
            ),
          ),
        )
        .value;
    final executionMetadata =
        testExecution?.executionMetadata ?? ExecutionMetadata();
    final filters = AttachmentRuleFilters(
      families: familyName.isNotEmpty ? [familyName] : [],
      testCaseNames: testCaseName.isNotEmpty ? [testCaseName] : [],
      templateIds: templateId.isNotEmpty ? [templateId] : [],
      executionMetadata: executionMetadata,
      testResultStatuses: TestResultStatus.values,
    );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Attachment Rule Filters',
          style: Theme.of(context).textTheme.titleLarge,
        ),
        AttachmentRuleFiltersWidget(
          filters: filters,
          editable: true,
          initialSelectedFilters: selectedFilters,
          onChanged: onChanged,
        ),
      ],
    );
  }
}
