import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/search_value.dart';
import '../vanilla/vanilla_search_bar.dart';

final artefactSearchBarKey = GlobalKey<_ArtefactSearchBarState>();

class ArtefactSearchBar extends ConsumerStatefulWidget {
  ArtefactSearchBar() : super(key: artefactSearchBarKey);

  @override
  ConsumerState<ArtefactSearchBar> createState() => _ArtefactSearchBarState();
}

class _ArtefactSearchBarState extends ConsumerState<ArtefactSearchBar> {
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
    return _SearchNotifierListener(
      child: VanillaSearchBar(
        focusNode: focusNode,
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
