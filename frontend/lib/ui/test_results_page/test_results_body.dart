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
import '../../providers/test_results_filters.dart';
import '../../providers/test_results_search.dart';
import '../../providers/global_error_message.dart';
import '../../routing.dart';
import 'test_results_table.dart';

final hasSearchedProvider = StateProvider<bool>((ref) => false);

class TestResultsBody extends ConsumerStatefulWidget {
  const TestResultsBody({super.key});

  @override
  ConsumerState<TestResultsBody> createState() => _TestResultsBodyState();
}

class _TestResultsBodyState extends ConsumerState<TestResultsBody> {
  final ScrollController _scrollController = ScrollController();

  bool _isLoadingMore = false;

  @override
  void initState() {
    super.initState();

    // Auto-search when URL contains query params.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final uri = AppRoutes.uriFromContext(context);
      if (uri.queryParameters.isNotEmpty) {
        ref
            .read(testResultsFiltersProvider.notifier)
            .loadFromQueryParams(uri.queryParametersAll);
        ref.read(testResultsSearchProvider.notifier).search();
      }
    });

    // Trigger load more when near the bottom.
    _scrollController.addListener(() {
      final pos = _scrollController.position;
      if (!pos.hasPixels || !pos.hasContentDimensions) return;

      // When at bottom, try loading more.
      final nearBottom = pos.pixels > (pos.maxScrollExtent - 600);
      if (nearBottom) _maybeLoadMore();
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    ref.listen<AsyncValue<TestResultsSearchResult>>(
      testResultsSearchProvider,
      (prev, next) {
        final wasLoading = prev?.isLoading ?? false;
        final finished = next.hasError || next.hasValue;
        if (wasLoading && finished) {
          ref.read(hasSearchedProvider.notifier).state = true;
        }
      },
    );

    final searchResults = ref.watch(testResultsSearchProvider);

    return searchResults.when(
      loading: () => Center(
        child: Transform.translate(
          offset: const Offset(0, -120),
          child: const YaruCircularProgressIndicator(),
        ),
      ),
      error: (error, stack) => Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              'Error loading test results',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              error.toString(),
              style: const TextStyle(color: Colors.red),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
      data: (data) => _buildResultsContent(context, data),
    );
  }

  Widget _buildResultsContent(
    BuildContext context,
    TestResultsSearchResult data,
  ) {
    final hasSearched = ref.watch(hasSearchedProvider);
    final count = data.count;
    final testResults = data.testResults;

    if (!hasSearched) {
      return Center(
        child: Transform.translate(
          offset: const Offset(0, -200),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.search, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              Text(
                'Search for test results',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              const Text(
                'Use the filters above and click Apply Filters to search for test results.',
                style: TextStyle(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    if (count == 0) {
      return Center(
        child: Transform.translate(
          offset: const Offset(0, -200),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.search_off, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              Text(
                'No results found',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const SizedBox(height: 8),
              const Text(
                'Try adjusting your search filters and try again.',
                style: TextStyle(color: Colors.grey),
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
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 12.0),
          child: Row(
            children: [
              Text(
                'Found $count results',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const Spacer(),
              if (data.hasMore && !_isLoadingMore)
                TextButton(
                  onPressed: _loadMore,
                  child: const Text(
                    'Load 100 more',
                    style: TextStyle(color: YaruColors.orange),
                  ),
                )
              else if (_isLoadingMore)
                Row(
                  children: const [
                    SizedBox(
                      width: 16,
                      height: 16,
                      child: YaruCircularProgressIndicator(strokeWidth: 2),
                    ),
                    SizedBox(width: 8),
                    Text('Loading...', style: TextStyle(color: Colors.grey)),
                  ],
                ),
            ],
          ),
        ),
        Expanded(
          child: NotificationListener<OverscrollIndicatorNotification>(
            onNotification: (n) {
              n.disallowIndicator();
              return false;
            },
            child: SingleChildScrollView(
              controller: _scrollController,
              padding: const EdgeInsets.only(bottom: 24),
              child: TestResultsTable(
                testResults: testResults,
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Manual button handler
  Future<void> _loadMore() async {
    if (_isLoadingMore) return;
    setState(() => _isLoadingMore = true);

    try {
      await ref.read(testResultsSearchProvider.notifier).loadMore();
    } catch (e) {
      if (mounted) {
        ref
            .read(globalErrorMessageProvider.notifier)
            .set('Failed to load more results. Please try again.');
      }
    } finally {
      if (mounted) {
        setState(() => _isLoadingMore = false);
      }
    }
  }

  void _maybeLoadMore() {
    if (_isLoadingMore) return;

    final data = ref.read(testResultsSearchProvider).valueOrNull;
    if (data == null || !data.hasMore) return;

    _loadMore();
  }
}
