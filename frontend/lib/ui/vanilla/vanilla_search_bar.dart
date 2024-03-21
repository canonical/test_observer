import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

class VanillaSearchBar extends StatefulWidget {
  const VanillaSearchBar({
    super.key,
    required this.onChanged,
    this.hintText,
    this.focusNode,
    this.initialText,
  });

  final String? hintText;
  final FocusNode? focusNode;
  final void Function(String)? onChanged;
  final String? initialText;

  @override
  State<VanillaSearchBar> createState() => _VanillaSearchBarState();
}

class _VanillaSearchBarState extends State<VanillaSearchBar> {
  late TextEditingController controller;

  @override
  void initState() {
    super.initState();
    controller = TextEditingController(text: widget.initialText);
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant VanillaSearchBar oldWidget) {
    super.didUpdateWidget(oldWidget);
    final initialText = widget.initialText;
    if (initialText != null && oldWidget.initialText != initialText) {
      controller.text = initialText;
    }
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      width: double.infinity,
      child: SearchBar(
        controller: controller,
        hintText: widget.hintText,
        hintStyle: MaterialStatePropertyAll(
          Theme.of(context)
              .textTheme
              .bodyLarge
              ?.apply(color: YaruColors.warmGrey),
        ),
        focusNode: widget.focusNode,
        elevation: const MaterialStatePropertyAll(0),
        shape: MaterialStatePropertyAll(LinearBorder.bottom()),
        side: const MaterialStatePropertyAll(BorderSide()),
        onChanged: widget.onChanged,
      ),
    );
  }
}
