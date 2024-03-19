import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/search_value.dart';
import '../focusable_search_bar.dart';

class ArtefactSearchBar extends ConsumerWidget {
  const ArtefactSearchBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return _SearchNotifierListener(
      child: FocusableSearchBar(
        onChanged: ref.read(searchValueProvider.notifier).onChanged,
        hintText: 'Search by name',
      ),
    );
  }
}

// Watches searchValueProvider as otherwise riverpod will not initialize it
// since it's not being watched by any widget
class _SearchNotifierListener extends ConsumerWidget {
  const _SearchNotifierListener({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    ref.watch(searchValueProvider);
    return child;
  }
}
