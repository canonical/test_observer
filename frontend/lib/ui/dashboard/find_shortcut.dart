import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/artefact_side_filters_visibility.dart';
import '../../routing.dart';
import '../page_search_bar.dart';

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
