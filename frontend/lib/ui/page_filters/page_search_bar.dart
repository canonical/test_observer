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
import 'package:go_router/go_router.dart';

import '../../providers/search_value.dart';
import '../../routing.dart';
import '../vanilla/vanilla_search_bar.dart';

final pageSearchBarKey = GlobalKey<_PageSearchBarState>();

class PageSearchBar extends ConsumerStatefulWidget {
  PageSearchBar({this.hintText, this.onSubmitted, this.onFocusRemoved})
      : super(key: pageSearchBarKey);

  final String? hintText;
  final void Function(String)? onSubmitted;
  final void Function()? onFocusRemoved;

  @override
  ConsumerState<PageSearchBar> createState() => _PageSearchBarState();
}

class _PageSearchBarState extends ConsumerState<PageSearchBar> {
  late FocusNode focusNode;

  @override
  void initState() {
    super.initState();
    focusNode = FocusNode();
    focusNode.addListener(_handleFocusChange);
  }

  void _handleFocusChange() {
    if (!focusNode.hasFocus && widget.onFocusRemoved != null) {
      widget.onFocusRemoved!();
    }
  }

  @override
  void dispose() {
    focusNode.removeListener(_handleFocusChange);
    focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final searchQuery = GoRouterState.of(context)
        .uri
        .queryParameters[CommonQueryParameters.searchQuery];

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
