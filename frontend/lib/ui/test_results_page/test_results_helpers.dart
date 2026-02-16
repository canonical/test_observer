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

import 'package:flutter/material.dart';

import '../../models/test_result.dart';

class TestResultHelpers {
  static TestResultStatus parseTestResultStatus(String? status) {
    switch (status?.toUpperCase()) {
      case 'PASSED':
        return TestResultStatus.passed;
      case 'FAILED':
        return TestResultStatus.failed;
      case 'SKIPPED':
        return TestResultStatus.skipped;
      default:
        return TestResultStatus.failed;
    }
  }

  static Widget getStatusIcon(TestResultStatus status) {
    return status.getIcon();
  }
}
