import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../providers/side_filters_visibility.dart';
import 'artefact_search_bar.dart';

class FindShortcut extends ConsumerWidget {
  const FindShortcut({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    const shortcut = SingleActivator(LogicalKeyboardKey.keyF, control: true);

    return Shortcuts(
      shortcuts: {shortcut: FindIntent()},
      child: Actions(
        actions: {FindIntent: FindAction(ref: ref)},
        child: child,
      ),
    );
  }
}

class FindIntent extends Intent {}

class FindAction extends Action<FindIntent> {
  FindAction({required this.ref});

  final WidgetRef ref;

  @override
  void invoke(FindIntent intent) {
    ref.read(sideFiltersVisibilityProvider.notifier).set(true);
    artefactSearchBarKey.currentState?.focusNode.requestFocus();
  }
}
