// Copyright 2024 Canonical Ltd.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License version 3, as
// published by the Free Software Foundation.
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.
//
// SPDX-FileCopyrightText: Copyright 2024 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:dartx/dartx.dart';
import 'package:flutter/material.dart';

import '../../models/test_execution.dart';
import '../../routing.dart';
import '../expandable.dart';
import 'test_execution_expandable/test_execution_expandable.dart';
import 'test_execution_expandable/test_execution_rerun_button.dart';

class TestPlanExpandable extends StatelessWidget {
  const TestPlanExpandable({
    super.key,
    required this.testExecutionsDescending,
    required this.artefactId,
    this.initiallyExpanded = false,
  });

  final bool initiallyExpanded;
  final int artefactId;
  final Iterable<TestExecution> testExecutionsDescending;

  @override
  Widget build(BuildContext context) {
    String title = testExecutionsDescending.first.testPlan;
    if (title.isEmpty) {
      title = TestExecution.defaultTestPlanName;
    }

    final pageUri = AppRoutes.uriFromContext(context);
    final targetTestExecutionId = pageUri.queryParameters['testExecutionId'];
    final targetId = int.tryParse(targetTestExecutionId ?? '');
    final shouldExpand = initiallyExpanded ||
        (targetId != null &&
            testExecutionsDescending.any((te) => te.id == targetId));

    return Expandable(
      initiallyExpanded: shouldExpand,
      title: Row(
        children: [
          Text(title),
          const Spacer(),
          RerunButton(testExecution: testExecutionsDescending.first),
        ],
      ),
      children: testExecutionsDescending
          .mapIndexed(
            (i, te) => TestExecutionExpandable(
              artefactId: artefactId,
              initiallyExpanded: targetId != null ? te.id == targetId : i == 0,
              testExecution: te,
              runNumber: testExecutionsDescending.length - i,
            ),
          )
          .toList(),
    );
  }
}
