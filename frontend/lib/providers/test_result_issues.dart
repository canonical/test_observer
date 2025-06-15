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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_issue.dart';
import '../models/test_result.dart';
import 'tests_issues.dart';

part 'test_result_issues.g.dart';

@riverpod
Future<List<TestIssue>> testResultIssues(Ref ref, TestResult testResult) {
  return ref.watch(
    testsIssuesProvider.selectAsync(
      (issues) => issues
          .filter(
            (issue) =>
                issue.caseName == testResult.name ||
                (issue.templateId == testResult.templateId &&
                    issue.templateId.isNotEmpty),
          )
          .toList(),
    ),
  );
}
