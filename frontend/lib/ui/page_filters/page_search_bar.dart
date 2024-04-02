import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../providers/search_value.dart';
import '../vanilla/vanilla_search_bar.dart';

final pageSearchBarKey = GlobalKey<_PageSearchBarState>();

class PageSearchBar extends ConsumerStatefulWidget {
  PageSearchBar({this.hintText, this.onSubmitted})
      : super(key: pageSearchBarKey);

  final String? hintText;
  final void Function(String)? onSubmitted;

  @override
  ConsumerState<PageSearchBar> createState() => _PageSearchBarState();
}

class _PageSearchBarState extends ConsumerState<PageSearchBar> {
  late FocusNode focusNode;

  @override
  void initState() {
    super.initState();
    focusNode = FocusNode();
  }

  @override
  void dispose() {
    focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final searchQuery = GoRouterState.of(context).uri.queryParameters['q'];

    return _SearchNotifierListener(
      searchQuery: searchQuery,
      child: VanillaSearchBar(
        focusNode: focusNode,
        onChanged:
            ref.read(searchValueProvider(searchQuery).notifier).onChanged,
        hintText: widget.hintText,
        initialText: searchQuery,
        onSubmitted: widget.onSubmitted,
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
