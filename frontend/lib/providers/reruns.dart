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

import 'package:riverpod_annotation/riverpod_annotation.dart';

import '../models/test_results_filters.dart';
import 'api.dart';

part 'reruns.g.dart';

@Riverpod(keepAlive: true)
class Reruns extends _$Reruns {
  @override
  int build() {
    // Return dummy state - this provider is used for its methods, not state
    return 0;
  }

  Future<void> createReruns({
    List<int>? testExecutionIds,
    TestResultsFilters? filters,
  }) async {
    final api = ref.read(apiProvider);
    await api.createReruns(
      testExecutionIds: testExecutionIds,
      filters: filters,
    );
  }

  Future<void> deleteReruns({
    List<int>? testExecutionIds,
    TestResultsFilters? filters,
  }) async {
    final api = ref.read(apiProvider);
    await api.deleteReruns(
      testExecutionIds: testExecutionIds,
      filters: filters,
    );
  }
}
