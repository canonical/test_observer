import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/search_value.dart';
import '../focusable_search_bar.dart';

class ArtefactSearchBar extends ConsumerWidget {
  const ArtefactSearchBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final searchQuery = GoRouterState.of(context).uri.queryParameters['q'];

    return _SearchNotifierListener(
      searchQuery: searchQuery,
      child: FocusableSearchBar(
        onChanged:
            ref.read(searchValueProvider(searchQuery).notifier).onChanged,
        hintText: 'Search by name',
        initialText: searchQuery,
      ),
    );
  }
}

// Watches searchValueProvider as otherwise riverpod will not initialize it
// since it's not being watched by any widget
class _SearchNotifierListener extends ConsumerWidget {
  const _SearchNotifierListener({required this.child, this.searchQuery});

  final Widget child;
  final String? searchQuery;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(searchValueProvider(searchQuery));
    return child;
  }
}
