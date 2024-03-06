import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/artefact_side_filters_visibility.dart';
import '../../routing.dart';
import 'artefact_search_bar.dart';

class FindShortcut extends ConsumerWidget {
  const FindShortcut({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final shouldActivateShortcut = AppRoutes.isAtDashboardPage(context);
    const shortcut = SingleActivator(LogicalKeyboardKey.keyF, control: true);

    if (shouldActivateShortcut) {
      return Shortcuts(
        shortcuts: {shortcut: FindIntent()},
        child: Actions(
          actions: {
            FindIntent: FindAction(
              setFiltersVisibility:
                  ref.read(artefactSideFiltersVisibilityProvider.notifier).set,
            ),
          },
          child: child,
        ),
      );
    } else {
      return child;
    }
  }
}

class FindIntent extends Intent {}

class FindAction extends Action<FindIntent> {
  FindAction({required this.setFiltersVisibility});

  final void Function(bool) setFiltersVisibility;

  @override
  void invoke(FindIntent intent) {
    setFiltersVisibility(true);
    artefactSearchBarKey.currentState?.focusNode.requestFocus();
  }
}
