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

import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/search_page_results.dart';
import '../models/test_results_filters.dart';
import 'api.dart';

final searchPageResultsProvider = StateNotifierProvider.autoDispose.family<
  SearchPageResultsController,
  AsyncValue<SearchPageResultsState>,
  TestResultsFilters
>((ref, filters) => SearchPageResultsController(ref: ref, filters: filters));

class SearchPageResultsController
    extends StateNotifier<AsyncValue<SearchPageResultsState>> {
  SearchPageResultsController({required Ref ref, required this.filters})
    : _ref = ref,
      super(
        filters.hasFilters
            ? const AsyncValue.loading()
            : const AsyncValue.data(SearchPageResultsState(count: 0, rows: [])),
      ) {
    if (filters.hasFilters) unawaited(loadInitial());
  }

  static const int pageSize = 100;

  final Ref _ref;
  final TestResultsFilters filters;
  bool _loadingMore = false;

  Future<void> loadInitial() async {
    state = const AsyncValue.loading();
    try {
      final response = await _ref
          .read(apiProvider)
          .searchTestResultsPage(
            filters,
            limit: pageSize,
            offset: 0,
            includeCount: true,
          );
      final count = response.count;
      if (count == null) {
        throw StateError('The first Search page response must include a count');
      }
      if (mounted) {
        state = AsyncValue.data(
          SearchPageResultsState(count: count, rows: response.rows),
        );
      }
    } catch (error, stackTrace) {
      if (mounted) state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> loadMore() async {
    final current = state.valueOrNull;
    if (_loadingMore || current == null || !current.hasMore) return;

    _loadingMore = true;
    state = const AsyncValue<SearchPageResultsState>.loading().copyWithPrevious(
      AsyncValue.data(current),
    );
    try {
      final response = await _ref
          .read(apiProvider)
          .searchTestResultsPage(
            filters,
            limit: pageSize,
            offset: current.rows.length,
            includeCount: false,
          );
      if (mounted) {
        state = AsyncValue.data(
          SearchPageResultsState(
            count: current.count,
            rows: [...current.rows, ...response.rows],
          ),
        );
      }
    } catch (error, stackTrace) {
      if (mounted) {
        state = AsyncValue<SearchPageResultsState>.error(
          error,
          stackTrace,
        ).copyWithPrevious(AsyncValue.data(current));
      }
    } finally {
      _loadingMore = false;
    }
  }
}
