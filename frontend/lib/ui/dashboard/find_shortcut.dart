import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'artefact_search_bar.dart';

class FindShortcut extends StatelessWidget {
  const FindShortcut({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    const shortcut = SingleActivator(LogicalKeyboardKey.keyF, control: true);

    return Shortcuts(
      shortcuts: {shortcut: FindIntent()},
      child: Actions(
        actions: {FindIntent: FindAction()},
        child: child,
      ),
    );
  }
}

class FindIntent extends Intent {}

class FindAction extends Action<FindIntent> {
  @override
  void invoke(FindIntent intent) =>
      artefactSearchBarKey.currentState?.focusNode.requestFocus();
}
