// Copyright 2025 Canonical Ltd.
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
// SPDX-FileCopyrightText: Copyright 2025 Canonical Ltd.
// SPDX-License-Identifier: GPL-3.0-only

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'api.dart';

part 'test_results_test_cases.g.dart';

@riverpod
Future<List<String>> suggestedTestCases(
  Ref ref,
  String query,
  List<String> families,
) async {
  // Only search if query is long enough
  if (query.trim().length < 2) {
    return [];
  }

  final api = ref.watch(apiProvider);
  return await api.searchTestCases(
    query: query.trim(),
    limit: 50,
    families: families.isNotEmpty ? families : null,
  );
}
