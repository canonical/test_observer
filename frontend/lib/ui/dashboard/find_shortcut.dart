// Copyright (C) 2023-2025 Canonical Ltd.
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
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/artefact_side_filters_visibility.dart';
import '../../routing.dart';
import '../page_filters/page_search_bar.dart';

class FindShortcut extends ConsumerWidget {
  const FindShortcut({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shouldMakeFiltersVisible =
        AppRoutes.isDashboardPage(AppRoutes.uriFromContext(context));
    const shortcut = SingleActivator(LogicalKeyboardKey.keyF, control: true);

    return Shortcuts(
      shortcuts: {shortcut: FindIntent()},
      child: Actions(
        actions: {
          FindIntent: FindAction(
            makeFiltersVisibile: shouldMakeFiltersVisible
                ? () => ref
                    .read(artefactSideFiltersVisibilityProvider.notifier)
                    .set(true)
                : () {},
          ),
        },
        child: child,
      ),
    );
  }
}

class FindIntent extends Intent {}

class FindAction extends Action<FindIntent> {
  FindAction({required this.makeFiltersVisibile});

  final void Function() makeFiltersVisibile;

  @override
  void invoke(FindIntent intent) {
    makeFiltersVisibile();
    pageSearchBarKey.currentState?.focusNode.requestFocus();
  }
}
