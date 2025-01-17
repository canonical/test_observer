// Copyright (C) 2024 Canonical Ltd.
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
import 'package:yaru/yaru.dart';

class VanillaSearchBar extends StatefulWidget {
  const VanillaSearchBar({
    super.key,
    required this.onChanged,
    this.hintText,
    this.focusNode,
    this.initialText,
    this.onSubmitted,
  });

  final String? hintText;
  final FocusNode? focusNode;
  final void Function(String)? onChanged;
  final String? initialText;
  final void Function(String)? onSubmitted;

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
        hintStyle: WidgetStatePropertyAll(
          Theme.of(context)
              .textTheme
              .bodyLarge
              ?.apply(color: YaruColors.warmGrey),
        ),
        focusNode: widget.focusNode,
        elevation: const WidgetStatePropertyAll(0),
        shape: WidgetStatePropertyAll(LinearBorder.bottom()),
        side: const WidgetStatePropertyAll(BorderSide()),
        onChanged: widget.onChanged,
        onSubmitted: widget.onSubmitted,
      ),
    );
  }
}
