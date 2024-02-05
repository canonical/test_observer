import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

class VanillaSearchBar extends StatelessWidget {
  const VanillaSearchBar({
    super.key,
    required this.onChanged,
    this.hintText,
    this.focusNode,
  });

  final String? hintText;
  final FocusNode? focusNode;
  final void Function(String)? onChanged;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      width: double.infinity,
      child: SearchBar(
        hintText: hintText,
        hintStyle: MaterialStatePropertyAll(
          Theme.of(context)
              .textTheme
              .bodyLarge
              ?.apply(color: YaruColors.warmGrey),
        ),
        focusNode: focusNode,
        elevation: const MaterialStatePropertyAll(0),
        shape: MaterialStatePropertyAll(LinearBorder.bottom()),
        side: const MaterialStatePropertyAll(BorderSide()),
        onChanged: onChanged,
      ),
    );
  }
}
