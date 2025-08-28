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

import '../../providers/test_results_filters.dart';
import '../../providers/test_results_search.dart';
import '../../routing.dart';
import '../spacing.dart';
import '../../providers/global_error_message.dart';
import 'test_results_table.dart';

final hasSearchedProvider = StateProvider<bool>((ref) => false);

class TestResultsBody extends ConsumerStatefulWidget {
  const TestResultsBody({super.key});

  @override
  ConsumerState<TestResultsBody> createState() => _TestResultsBodyState();
}

class _TestResultsBodyState extends ConsumerState<TestResultsBody> {
  final Map<String, bool> _expandedItems = {};
  final ScrollController _scrollController = ScrollController();

  bool _isLoadingMore = false;

  @override
  void initState() {
    super.initState();
    // Check if we have URL parameters and auto-search if we do
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final uri = AppRoutes.uriFromContext(context);
      if (uri.queryParameters.isNotEmpty) {
        ref
            .read(testResultsFiltersProvider.notifier)
            .loadFromQueryParams(uri.queryParametersAll);
        ref.read(testResultsSearchProvider.notifier).search();
      }
    });
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _toggleExpanded(String key) {
    setState(() {
      _expandedItems[key] = !(_expandedItems[key] ?? false);
    });
  }

  bool _isExpanded(String key) {
    if (key.startsWith('family_')) {
      return _expandedItems[key] ?? true;
    }
    return _expandedItems[key] ?? false;
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
                'Click "Apply Filters" to search test results',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Select your desired filters and click Apply to see results',
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
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.search_off, size: 64, color: Colors.grey),
              const SizedBox(height: 16),
              Text(
                'No test results found',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              const Text(
                'Try adjusting your search filters',
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
          padding: const EdgeInsets.all(Spacing.level4),
          child: Row(
            children: [
              Text(
                'Found $count test results',
                style: Theme.of(context).textTheme.headlineSmall,
              ),
              const Spacer(),
              if (testResults.length < count && !_isLoadingMore) ...[
                TextButton(
                  onPressed: () => _loadMore(),
                  child: const Text(
                    'Load 500 more',
                    style: TextStyle(color: YaruColors.orange),
                  ),
                ),
              ] else if (_isLoadingMore) ...[
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: YaruCircularProgressIndicator(strokeWidth: 2),
                ),
                const SizedBox(width: Spacing.level2),
                const Text('Loading...', style: TextStyle(color: Colors.grey)),
              ],
            ],
          ),
        ),
        Expanded(
          child: _buildTreeView(testResults),
        ),
      ],
    );
  }

  Widget _buildTreeView(List<Map<String, dynamic>> testResults) {
    final groupedResults = _groupTestResults(testResults);

    return ListView(
      controller: _scrollController,
      padding: const EdgeInsets.symmetric(horizontal: Spacing.level4),
      children: groupedResults.entries
          .map(
            (familyEntry) =>
                _buildFamilyNode(context, familyEntry.key, familyEntry.value),
          )
          .toList(),
    );
  }

  Map<String, List<Map<String, dynamic>>> _groupTestResults(
    List<Map<String, dynamic>> results,
  ) {
    final grouped = <String, List<Map<String, dynamic>>>{};

    for (final result in results) {
      final testResult = result['test_result'] as Map<String, dynamic>?;
      final testExecution = result['test_execution'] as Map<String, dynamic>?;
      final artefact = result['artefact'] as Map<String, dynamic>?;

      if (testResult == null || testExecution == null || artefact == null) {
        continue;
      }

      final family = artefact['family'] as String? ?? 'unknown';

      grouped.putIfAbsent(family, () => []);
      grouped[family]!.add(result);
    }

    return grouped;
  }

  Widget _buildFamilyNode(
    BuildContext context,
    String family,
    List<Map<String, dynamic>> results,
  ) {
    final familyKey = 'family_$family';
    final isExpanded = _isExpanded(familyKey);
    final totalResults = results.length;

    return Container(
      margin: const EdgeInsets.only(bottom: Spacing.level2),
      child: Column(
        children: [
          ListTile(
            leading: Icon(
              isExpanded
                  ? Icons.keyboard_arrow_down
                  : Icons.keyboard_arrow_right,
              color: isExpanded ? YaruColors.orange : null,
            ),
            title: Text(
              family.toUpperCase(),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(
                  Icons.play_arrow,
                  size: 16,
                  color: YaruColors.orange,
                ),
                const SizedBox(width: 4),
                Text('$totalResults'),
              ],
            ),
            onTap: () => _toggleExpanded(familyKey),
          ),
          if (isExpanded) ...[
            const Divider(height: 1),
            Padding(
              padding: const EdgeInsets.only(left: Spacing.level4),
              child: TestResultsTable(testResults: results),
            ),
          ],
        ],
      ),
    );
  }

  void _loadMore() async {
    if (_isLoadingMore) return;

    setState(() {
      _isLoadingMore = true;
    });

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
        setState(() {
          _isLoadingMore = false;
        });
      }
    }
  }
}
