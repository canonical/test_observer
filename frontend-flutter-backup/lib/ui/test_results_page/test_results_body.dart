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
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:yaru/yaru.dart';

import '../../models/detailed_test_results.dart';
import '../../models/test_results_filters.dart';
import '../../providers/test_results_search.dart';
import '../spacing.dart';
import 'test_results_table.dart';

class TestResultsBody extends ConsumerStatefulWidget {
  const TestResultsBody({super.key, required this.filters});

  final TestResultsFilters filters;

  @override
  ConsumerState<TestResultsBody> createState() => _TestResultsBodyState();
}

class _TestResultsBodyState extends ConsumerState<TestResultsBody> {
  final ScrollController _scrollController = ScrollController();
  bool _isLoadingMore = false;
  TestResultsFilters? _lastProcessedFilters;

  @override
  void initState() {
    super.initState();

    _scrollController.addListener(_onScroll);
  }

  @override
  void didUpdateWidget(TestResultsBody oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Handle URI changes
    if (oldWidget.filters != widget.filters) {
      _handleFiltersChange();
    }
  }

  @override
  void dispose() {
    _scrollController.removeListener(_onScroll);
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.extentAfter < 800) {
      _maybeLoadMore();
    }
  }

  void _handleFiltersChange() {
    if (widget.filters != _lastProcessedFilters) {
      _lastProcessedFilters = widget.filters;
    }
  }

  Future<void> _loadMore() async {
    if (_isLoadingMore) return;
    setState(() => _isLoadingMore = true);

    try {
      await ref
          .read(testResultsSearchProvider(widget.filters).notifier)
          .loadMore();
    } finally {
      if (mounted) {
        setState(() => _isLoadingMore = false);
      }
    }
  }

  void _maybeLoadMore() {
    if (_isLoadingMore) return;

    final data =
        ref.read(testResultsSearchProvider(widget.filters)).valueOrNull;
    if (data == null || !data.hasMore) return;

    _loadMore();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.filters.hasFilters) {
      return _buildEmptyState(context);
    }

    final searchResults = ref.watch(testResultsSearchProvider(widget.filters));

    return searchResults.when(
      loading: () => _buildLoadingState(context),
      error: (error, stack) => _buildErrorState(context, error),
      data: (data) => _buildResultsContent(context, data),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.only(
          bottom: Spacing.level6 * 4,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.search, size: 64, color: Colors.grey),
            const SizedBox(height: Spacing.level4),
            Text(
              'Search for test results',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: Spacing.level2),
            const Text(
              'Use the filters above and click Apply Filters to search for test results.',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildLoadingState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.only(
          bottom: Spacing.level6 * 4,
        ),
        child: const YaruCircularProgressIndicator(),
      ),
    );
  }

  Widget _buildErrorState(BuildContext context, Object error) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.only(
          bottom: Spacing.level6 * 4,
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: Spacing.level4),
            Text(
              'Error loading test results',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: Spacing.level2),
            Text(
              error.toString(),
              style: const TextStyle(color: Colors.red),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildResultsContent(
    BuildContext context,
    TestResultsSearchResult data,
  ) {
    final count = data.count;
    final testResults = data.testResults;

    if (testResults.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.only(
            bottom: Spacing.level6 * 4,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.search_off, size: 64, color: Colors.grey),
              const SizedBox(height: Spacing.level4),
              Text(
                'No results found',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: Spacing.level2),
              const Text(
                'Try adjusting your filters or search criteria.',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              'Found $count results (showing ${testResults.length})',
              style: Theme.of(context).textTheme.bodyLarge,
            ),
            if (_isLoadingMore) ...[
              const SizedBox(width: 16),
              const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ],
          ],
        ),
        const SizedBox(height: Spacing.level3),
        Expanded(
          child: NotificationListener<ScrollNotification>(
            onNotification: (ScrollNotification scrollInfo) {
              final screenHeight = MediaQuery.of(context).size.height;
              // Load more naturally when the scroll is at the bottom
              if (scrollInfo.metrics.extentAfter < screenHeight * 0.5) {
                _maybeLoadMore();
              }
              return false;
            },
            child: CustomScrollView(
              controller: _scrollController,
              slivers: [
                SliverToBoxAdapter(
                  child: TestResultsTable(
                    testResults: testResults,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
