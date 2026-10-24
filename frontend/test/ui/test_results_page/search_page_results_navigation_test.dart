// Copyright 2026 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2026 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_test/flutter_test.dart';
import 'package:testcase_dashboard/models/search_page_results.dart';
import 'package:testcase_dashboard/ui/test_results_page/search_page_results_navigation.dart';

import '../../search_page_test_data.dart';

void main() {
  test(
    'View Run path preserves family and selected run/result identifiers',
    () {
      final row = SearchPageTableRow.fromJson(
        searchPageRowJson(id: 23, executionId: 12),
      );

      expect(
        searchPageRunPath(row),
        '/snaps/7?testExecutionId=12&testResultId=23',
      );
    },
  );
}
