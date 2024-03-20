import 'package:flutter/material.dart';

import 'vanilla/vanilla_search_bar.dart';

final focusableSearchBarKey = GlobalKey<_FocusableSearchBarState>();

class FocusableSearchBar extends StatefulWidget {
  FocusableSearchBar({this.onChanged, this.hintText, this.initialText})
      : super(key: focusableSearchBarKey);

  final void Function(String)? onChanged;
  final String? hintText;
  final String? initialText;

  @override
  State<FocusableSearchBar> createState() => _FocusableSearchBarState();
}

class _FocusableSearchBarState extends State<FocusableSearchBar> {
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
    return VanillaSearchBar(
      focusNode: focusNode,
      onChanged: widget.onChanged,
      hintText: widget.hintText,
      initialText: widget.initialText,
    );
  }
}
