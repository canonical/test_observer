import 'package:flutter/material.dart';
import 'package:yaru/yaru.dart';

class VanillaSearchBar extends StatelessWidget {
  const VanillaSearchBar({super.key, required this.onChanged, this.hintText});

  final void Function(String)? onChanged;
  final String? hintText;

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
        elevation: const MaterialStatePropertyAll(0),
        shape: MaterialStatePropertyAll(LinearBorder.bottom()),
        side: const MaterialStatePropertyAll(BorderSide()),
        onChanged: onChanged,
      ),
    );
  }
}
